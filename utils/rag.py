from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import fitz
import os

class RAGProcessor:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chunks = []
        self.faiss_index = None
    
    def extract_text_from_pdf(self, pdf_file):
        """Extract text from PDF file"""
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    
    def chunk_text(self, text, chunk_size=300, overlap=50):
        """Split text into chunks with overlap"""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks
    
    def embed_chunks(self, chunks):
        """Generate embeddings for chunks"""
        return self.model.encode(chunks, show_progress_bar=True)
    
    def create_faiss_index(self, vectors):
        """Create FAISS index for vector search"""
        dimension = vectors.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(vectors)
        return index
    
    def retrieve_top_chunks(self, query, k=5):
        """Retrieve top k relevant chunks for a query"""
        if not self.faiss_index or not self.chunks:
            return []
        
        query_vec = self.model.encode([query])
        D, I = self.faiss_index.search(query_vec, k)
        return [self.chunks[i] for i in I[0]]
    
    def process_document(self, pdf_file):
        """Process PDF document and create searchable index"""
        try:
            # Extract text
            text = self.extract_text_from_pdf(pdf_file)
            
            if not text.strip():
                raise ValueError("No text content found in PDF")
            
            # Create chunks
            self.chunks = self.chunk_text(text)
            
            if not self.chunks:
                raise ValueError("No chunks created from text")
            
            # Generate embeddings
            vectors = self.embed_chunks(self.chunks)
            vectors = np.array(vectors)
            
            if vectors.ndim != 2:
                raise ValueError(f"Invalid embedding shape: {vectors.shape}")
            
            # Create FAISS index
            self.faiss_index = self.create_faiss_index(vectors)
            
            return True
            
        except Exception as e:
            print(f"Error processing document: {e}")
            return False