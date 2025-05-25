from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.models import Chat, User, Boy, Game
from ..schemas.schemas import ChatCreate, Chat as ChatSchema
from ..services.game import game_service

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ChatSchema)
async def send_message(chat: ChatCreate, user_id: int, db: Session = Depends(get_db)):
    """Send a message to a boy and get a response."""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Send message and get response
    response = await game_service.send_message(
        db=db,
        user_id=user_id,
        game_id=chat.game_id,
        boy_id=chat.boy_id,
        message=chat.message
    )
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to send message. Make sure you are in the game and the boy exists."
        )
    
    return response

@router.get("/history/{game_id}/{user_id}/{boy_id}", response_model=List[ChatSchema])
async def get_chat_history(game_id: int, user_id: int, boy_id: int, db: Session = Depends(get_db)):
    """Get chat history between a user and a boy in a game."""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if boy exists
    boy = db.query(Boy).filter(Boy.id == boy_id).first()
    if not boy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Boy not found"
        )
    
    # Check if game exists
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )
    
    # Get chat history
    chats = db.query(Chat).filter(
        Chat.game_id == game_id,
        Chat.user_id == user_id,
        Chat.boy_id == boy_id
    ).order_by(Chat.created_at).all()
    
    return chats