from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.chat_service import chat_service
from routers.auth import get_current_user
from models import User

router = APIRouter(
    tags=["chat"]
)

class ChatRequest(BaseModel):
    message: str
    context: str = ""

class ChatResponse(BaseModel):
    response: str

@router.post("/", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send a message to the Gemini-powered Career Coach.
    """
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    response_text = await chat_service.get_chat_response(request.message, request.context)
    return ChatResponse(response=response_text)
