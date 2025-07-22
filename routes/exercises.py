from controller.generateExercise import GenerateExercise
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from pydantic import BaseModel
from typing import Optional
import logging
from controller import supabase
from utils.helper import parse_mcq_text, parse_sqs_text, parse_lqs_text, parse_blanks_text, parse_true_false_text

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExerciseRequest(BaseModel):
    userId: str
    topic: str
    exercise_type: Optional[str] = "mcq"
    difficulty_level: Optional[str] = "medium"
    num_questions: Optional[int] = 5

class QuestionRequest(BaseModel):
    userId: str
    question: str

@router.post("/exercise/upload-book")
async def upload_book(userId: str = Form(...), file: UploadFile = File(...)):
    """Upload and process a PDF book for exercise generation"""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        exercise_generator = GenerateExercise(userId)
        result = exercise_generator.upload_and_process_book(file.file)
        
        if result["status"] == "success":
            return {"message": result["message"]}
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/exercise/generate")
async def generate_exercise(request: ExerciseRequest):
    """Generate exercises based on uploaded book content"""
    try:
        logger.info(f"Received generate_exercise request: {request}")
        exercise_generator = GenerateExercise(request.userId)
        exercises = exercise_generator.generate_exercise_with_context(
            topic=request.topic,
            exercise_type=request.exercise_type,
            num_questions=request.num_questions,
            difficulty_level=request.difficulty_level
        )
        logger.info(f"Generated exercises: {exercises}")
        # If MCQ, parse to array
        if request.exercise_type.lower() in ["multiple choice", "mcq", "mcqs"]:
            if isinstance(exercises, str):
                exercises = parse_mcq_text(exercises)
        # If True/False, parse to array
        elif request.exercise_type.lower() in ["true/false", "true_false", "true false", "tf"]:
            if isinstance(exercises, str):
                exercises = parse_true_false_text(exercises)
        # If SQS, parse to array
        elif request.exercise_type.lower() in ["short answer", "short_questions", "short question", "sqs"]:
            if isinstance(exercises, str):
                exercises = parse_sqs_text(exercises)
        # If LQS, parse to array
        elif request.exercise_type.lower() in ["long questions", "long_questions", "long question", "lqs"]:
            if isinstance(exercises, str):
                exercises = parse_lqs_text(exercises)
        # If Fill in the Blanks, parse to array
        elif request.exercise_type.lower() in ["fill in the blanks", "fill_blanks", "fill blank", "blanks"]:
            if isinstance(exercises, str):
                exercises = parse_blanks_text(exercises)
        if not exercises:
            exercises = "Sorry, no exercises could be generated."
        return {"exercises": exercises}
    except Exception as e:
        logger.error(f"Error in generate_exercise: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/exercise/ask")
async def ask_question_about_book(request: QuestionRequest):
    """Ask a question about the uploaded book"""
    try:
        exercise_generator = GenerateExercise(request.userId)
        answer = exercise_generator.ask_question_about_book(request.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/exercise/generate-simple")
async def generate_simple_exercise(request: ExerciseRequest):
    """Generate exercises without book context"""
    try:
        exercise_generator = GenerateExercise(request.userId)
        exercises = exercise_generator.generate_exercise_without_context(
            topic=request.topic,
            exercise_type=request.exercise_type,
            num_questions=request.num_questions
        )
        # If MCQ, parse to array
        if request.exercise_type.lower() in ["multiple choice", "mcq", "mcqs"]:
            if isinstance(exercises, str):
                exercises = parse_mcq_text(exercises)
        # If True/False, parse to array
        elif request.exercise_type.lower() in ["true/false", "true_false", "true false", "tf"]:
            if isinstance(exercises, str):
                exercises = parse_true_false_text(exercises)
        # If SQS, parse to array
        elif request.exercise_type.lower() in ["short answer", "short_questions", "short question", "sqs"]:
            if isinstance(exercises, str):
                exercises = parse_sqs_text(exercises)
        # If LQS, parse to array
        elif request.exercise_type.lower() in ["long questions", "long_questions", "long question", "lqs"]:
            if isinstance(exercises, str):
                exercises = parse_lqs_text(exercises)
        # If Fill in the Blanks, parse to array
        elif request.exercise_type.lower() in ["fill in the blanks", "fill_blanks", "fill blank", "blanks"]:
            if isinstance(exercises, str):
                exercises = parse_blanks_text(exercises)
        return {"exercises": exercises}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/exercise/save")
async def save_exercise(
    exerciseType: str = Body(...),
    exerciseData: list = Body(...),
    grade: str = Body(None),
    subject: str = Body(None),
    topic: str = Body(None),
    sub_topic: str = Body(None)
):
    """Save generated exercises to the appropriate table."""
    try:
        if exerciseType.lower() in ["multiple choice", "mcq", "mcqs"]:
            for ex in exerciseData:
                if not ex.get("question"):
                    continue
                mcq = {
                    "grade": grade,
                    "subject": subject,
                    "topic": topic,
                    "sub_topic": sub_topic,
                    "question": ex["question"],
                    "options": ex.get("options", []),  # Store as JSON
                    "correct_answer": ex.get("correct", "")  # Store as text
                }
                supabase.table("mcqs").insert(mcq).execute()
        elif exerciseType.lower() in ["fill in the blanks", "fill_blanks", "fill blank", "blanks"]:
            for ex in exerciseData:
                if not ex.get("question"):
                    continue
                fill_blank = {
                    "grade": grade,
                    "subject": subject,
                    "topic": topic,
                    "sub_topic": sub_topic,
                    "question": ex["question"],
                    "answer": ex.get("answer", "")
                }
                supabase.table("fill_blanks").insert(fill_blank).execute()
        elif exerciseType.lower() in ["short answer", "short_questions", "short question", "sqs"]:
            for ex in exerciseData:
                if not ex.get("question"):
                    continue
                short_q = {
                    "grade": grade,
                    "subject": subject,
                    "topic": topic,
                    "sub_topic": sub_topic,
                    "question": ex["question"]
                }
                supabase.table("short_questions").insert(short_q).execute()
        elif exerciseType.lower() in ["long questions", "long_questions", "long question", "lqs"]:
            for ex in exerciseData:
                if not ex.get("question"):
                    continue
                long_q = {
                    "grade": grade,
                    "subject": subject,
                    "topic": topic,
                    "sub_topic": sub_topic,
                    "question": ex["question"]
                }
                supabase.table("long_questions").insert(long_q).execute()
        elif exerciseType.lower() in ["true/false", "true_false", "true false", "tf"]:
            for ex in exerciseData:
                if not ex.get("question"):
                    continue
                tf_q = {
                    "grade": grade,
                    "subject": subject,
                    "topic": topic,
                    "sub_topic": sub_topic,
                    "question": ex["question"],
                    "answer": ex.get("answer", "")
                }
                supabase.table("true_false").insert(tf_q).execute()
        elif exerciseType.lower() in ["match the columns", "match_columns", "match the column", "match columns"]:
            for ex in exerciseData:
                if not ex.get("columnA") or not ex.get("columnB"):
                    continue
                match_columns = {
                    "grade": grade,
                    "subject": subject,
                    "topic": topic,
                    "sub_topic": sub_topic,
                    "columna": ex.get("columnA", []),  # Store as JSON
                    "columnb": ex.get("columnB", []),  # Store as JSON
                    "answers": ex.get("answers", {})  # Store as JSON (mapping)
                }
                supabase.table("match_columns").insert(match_columns).execute()
        elif exerciseType.lower() in ["flashcards", "flashcard"]:
            for ex in exerciseData:
                if not ex.get("question"):
                    continue
                flashcard = {
                    "grade": grade,
                    "subject": subject,
                    "topic": topic,
                    "sub_topic": sub_topic,
                    "question": ex.get("question", ""),
                    "hint": ex.get("hint", ""),
                    "answer": ex.get("answer", "")
                }
                supabase.table("flashcards").insert(flashcard).execute()
        else:
            print("Saving as generic exercise:", exerciseData)
        return {"message": "Exercises saved successfully!"}
    except Exception as e:
        print(f"Error saving exercises: {e}")
        raise HTTPException(status_code=500, detail=str(e))