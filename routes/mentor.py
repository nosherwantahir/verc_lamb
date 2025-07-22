from controller.mentorController import Mentor
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    userId: str
    message: str

@router.post("/mentor/chat")
async def chat_with_mentor(request: ChatRequest):
    try:
        mentor = Mentor(request.userId)
        response = mentor.chat_with_mentor(request.userId, request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mentor/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 50):
    try:
        mentor = Mentor(user_id)
        history = mentor.get_chat_history(user_id, limit)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))