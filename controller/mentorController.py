import google.generativeai as genai
from google.generativeai import types
import os
import dotenv 
import uuid
from datetime import datetime
from . import supabase  # Import the supabase client from __init__.py
from model.ai_chats import ChatConversationModel

dotenv.load_dotenv()

class Mentor:
    def __init__(self, userId):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        self.supabase = supabase  # Use the configured supabase client
        
        # Initialize the chat model and ensure table exists
        self.chat_model = ChatConversationModel(self.supabase)
        self.chat_model.ensure_table_exists()
    
    def chat_with_mentor(self, userId, message):
        try:
            system_instruction = os.getenv("MENTOR_SYSTEM_INSTRUCTION")
            full_message = f"{system_instruction}\n\n{message}" if system_instruction else message
            response = self.model.generate_content(
                contents=full_message,
                generation_config=types.GenerationConfig(
                    # Add other config params here if needed
                )
            )
            
            ai_response = response.text
            
            # Save conversation using the model
            saved_conversation = self.chat_model.insert_conversation(
                user_id=userId,
                user_message=message,
                mentor_response=ai_response
            )
            
            if saved_conversation:
                print("Conversation saved successfully")
            else:
                print("Failed to save conversation, but continuing...")
            
            return ai_response
            
        except Exception as e:
            print(f"Error in chat_with_mentor: {e}")
            return response.text if 'response' in locals() else "Sorry, there was an error processing your request."
    
    def get_chat_history(self, userId, limit=50):
        """Retrieve chat history for a user"""
        return self.chat_model.get_user_conversations(userId, limit)
