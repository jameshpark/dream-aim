from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime

from app.database.database import get_db
from app.models import models
from app.schemas import schemas
from app.routers.users import get_current_user
from app.routers.game import generate_buddy_response

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

# Routes
@router.get("/messages", response_model=List[schemas.Message])
async def get_chat_messages(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get chat messages for the current user's location (chat room or active round)
    """
    # Get messages from users in the same location
    messages = db.query(models.Message).join(
        models.User, models.Message.user_id == models.User.id
    ).filter(
        models.User.location == current_user.location
    ).order_by(
        models.Message.timestamp.desc()
    ).offset(skip).limit(limit).all()

    return messages

@router.post("/messages", response_model=schemas.Message)
async def create_chat_message(
    message: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new chat message
    """
    # Ensure the user is creating a message for themselves
    if message.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to create messages for other users")

    # Create the message
    db_message = models.Message(
        user_id=current_user.id,
        content=message.content,
        timestamp=datetime.now()
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    return db_message

@router.get("/users", response_model=List[schemas.User])
async def get_chat_room_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all users in the chat room
    """
    users = db.query(models.User).filter(
        models.User.location == schemas.UserLocation.CHAT_ROOM
    ).all()

    return users

@router.get("/active-round-users", response_model=List[schemas.User])
async def get_active_round_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all users in the active round
    """
    if current_user.location != schemas.UserLocation.ACTIVE_ROUND:
        raise HTTPException(status_code=403, detail="Not in an active round")

    users = db.query(models.User).filter(
        models.User.location == schemas.UserLocation.ACTIVE_ROUND,
        models.User.current_round_id == current_user.current_round_id
    ).all()

    return users

@router.get("/leader", response_model=Optional[schemas.User])
async def get_chat_room_leader(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get the current leader in the chat room
    """
    leader = db.query(models.User).filter(
        models.User.location == schemas.UserLocation.CHAT_ROOM,
        models.User.role == schemas.UserRole.LEADER
    ).first()

    return leader

@router.post("/conversations", response_model=schemas.Conversation)
async def create_conversation(
    conversation: schemas.ConversationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new conversation with a buddy
    """
    # Ensure the user is creating a conversation for themselves
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to create conversations for other users")

    # Ensure the user is in an active round
    if current_user.location != schemas.UserLocation.ACTIVE_ROUND:
        raise HTTPException(status_code=403, detail="Not in an active round")

    # Check if the buddy exists
    buddy = db.query(models.Buddy).filter(models.Buddy.id == conversation.buddy_id).first()
    if not buddy:
        raise HTTPException(status_code=404, detail="Buddy not found")

    # Check if the round exists
    game_round = db.query(models.Round).filter(models.Round.id == conversation.round_id).first()
    if not game_round:
        raise HTTPException(status_code=404, detail="Round not found")

    # Check if a conversation already exists
    existing_conversation = db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id,
        models.Conversation.buddy_id == conversation.buddy_id,
        models.Conversation.round_id == conversation.round_id
    ).first()

    if existing_conversation:
        return existing_conversation

    # Create the conversation
    db_conversation = models.Conversation(
        user_id=current_user.id,
        buddy_id=conversation.buddy_id,
        round_id=conversation.round_id,
        created_at=datetime.now()
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)

    return db_conversation

@router.get("/conversations", response_model=List[schemas.Conversation])
async def get_conversations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all conversations for the current user in the current round
    """
    if current_user.location != schemas.UserLocation.ACTIVE_ROUND:
        raise HTTPException(status_code=403, detail="Not in an active round")

    conversations = db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id,
        models.Conversation.round_id == current_user.current_round_id
    ).all()

    return conversations

@router.get("/conversations/{conversation_id}", response_model=schemas.Conversation)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get a specific conversation
    """
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation

@router.post("/conversations/{conversation_id}/messages", response_model=schemas.ConversationMessage)
async def create_conversation_message(
    conversation_id: int,
    message: schemas.ConversationMessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new message in a conversation
    """
    # Ensure the user is in an active round
    if current_user.location != schemas.UserLocation.ACTIVE_ROUND:
        raise HTTPException(status_code=403, detail="Not in an active round")

    # Ensure the conversation exists and belongs to the user
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Create the message
    db_message = models.ConversationMessage(
        conversation_id=conversation_id,
        sender_type=message.sender_type,
        content=message.content,
        timestamp=datetime.now()
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    # Generate a response from the buddy in the background
    background_tasks.add_task(
        generate_buddy_response,
        conversation_id,
        message.content,
        db
    )

    return db_message

@router.get("/conversations/{conversation_id}/messages", response_model=List[schemas.ConversationMessage])
async def get_conversation_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get messages from a conversation
    """
    # Ensure the conversation exists and belongs to the user
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get the messages
    messages = db.query(models.ConversationMessage).filter(
        models.ConversationMessage.conversation_id == conversation_id
    ).order_by(
        models.ConversationMessage.timestamp.asc()
    ).offset(skip).limit(limit).all()

    return messages
