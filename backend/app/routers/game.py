from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from typing import List, Dict, Optional
from datetime import datetime
import random
import openai
import os

from app.database.database import get_db
from app.models import models
from app.schemas import schemas
from app.routers.users import get_current_user

load_dotenv()

# OpenAI API key - in production, use environment variables
openai.api_key = os.getenv("OPENAI_API_KEY", "your-openai-api-key")

router = APIRouter(
    prefix="/game",
    tags=["game"],
    responses={404: {"description": "Not found"}},
)

# Helper functions
async def generate_buddy_response(conversation_id: int, user_message: str, db: Session):
    """
    Generate a response from a buddy using GPT-4o
    """
    # Get the conversation
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        return
    
    # Get the buddy
    buddy = db.query(models.Buddy).filter(
        models.Buddy.id == conversation.buddy_id
    ).first()
    
    if not buddy:
        return
    
    # Get the round
    game_round = db.query(models.Round).filter(
        models.Round.id == conversation.round_id
    ).first()
    
    if not game_round:
        return
    
    # Get all previous messages in the conversation
    messages = db.query(models.ConversationMessage).filter(
        models.ConversationMessage.conversation_id == conversation_id
    ).order_by(
        models.ConversationMessage.timestamp.asc()
    ).all()
    
    # Prepare the conversation history for GPT-4o
    conversation_history = []
    
    # Add the system prompt
    is_secret_admirer = buddy.id == game_round.secret_admirer
    system_prompt = f"{buddy.prompt}\n\nYou are {'the secret admirer' if is_secret_admirer else 'not the secret admirer'}. The secret admirer in this round is buddy #{game_round.secret_admirer}."
    conversation_history.append({"role": "system", "content": system_prompt})
    
    # Add the conversation history
    for message in messages:
        role = "user" if message.sender_type == "user" else "assistant"
        conversation_history.append({"role": role, "content": message.content})
    
    # Add the current user message
    conversation_history.append({"role": "user", "content": user_message})
    
    try:
        # Call GPT-4o
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=conversation_history,
            max_tokens=500,
            temperature=0.7
        )
        
        # Extract the response
        buddy_response = response.choices[0].message.content
        
        # Save the buddy's response
        db_message = models.ConversationMessage(
            conversation_id=conversation_id,
            sender_type="buddy",
            content=buddy_response,
            timestamp=datetime.now()
        )
        db.add(db_message)
        db.commit()
        
        return buddy_response
    
    except Exception as e:
        print(f"Error generating buddy response: {e}")
        return "Sorry, I'm having trouble responding right now."

# Routes
@router.get("/rounds", response_model=List[schemas.Round])
async def get_rounds(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all game rounds
    """
    rounds = db.query(models.Round).order_by(
        models.Round.start_time.desc()
    ).offset(skip).limit(limit).all()
    
    return rounds

@router.get("/rounds/active", response_model=Optional[schemas.Round])
async def get_active_round(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get the currently active round
    """
    active_round = db.query(models.Round).filter(
        models.Round.state == schemas.RoundState.ACTIVE
    ).first()
    
    return active_round

@router.post("/rounds", response_model=schemas.Round)
async def create_round(
    game_round: schemas.RoundCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new game round (leader only)
    """
    # Ensure the user is a leader
    if current_user.role != schemas.UserRole.LEADER:
        raise HTTPException(status_code=403, detail="Only leaders can create rounds")
    
    # Ensure the user is in the chat room
    if current_user.location != schemas.UserLocation.CHAT_ROOM:
        raise HTTPException(status_code=403, detail="Must be in the chat room to create a round")
    
    # Check if there's already an active round
    active_round = db.query(models.Round).filter(
        models.Round.state == schemas.RoundState.ACTIVE
    ).first()
    
    if active_round:
        raise HTTPException(status_code=400, detail="There is already an active round")
    
    # Create the round
    db_round = models.Round(
        state=schemas.RoundState.ACTIVE,
        start_time=datetime.now(),
        secret_admirer=game_round.secret_admirer
    )
    db.add(db_round)
    db.commit()
    db.refresh(db_round)
    
    return db_round

@router.post("/rounds/{round_id}/start", response_model=schemas.Round)
async def start_round(
    round_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Start a round and move all users in the chat room to the round
    """
    # Ensure the user is a leader
    if current_user.role != schemas.UserRole.LEADER:
        raise HTTPException(status_code=403, detail="Only leaders can start rounds")
    
    # Ensure the user is in the chat room
    if current_user.location != schemas.UserLocation.CHAT_ROOM:
        raise HTTPException(status_code=403, detail="Must be in the chat room to start a round")
    
    # Get the round
    game_round = db.query(models.Round).filter(models.Round.id == round_id).first()
    if not game_round:
        raise HTTPException(status_code=404, detail="Round not found")
    
    # Ensure the round is not already active
    if game_round.state == schemas.RoundState.ACTIVE:
        raise HTTPException(status_code=400, detail="Round is already active")
    
    # Get all users in the chat room
    chat_room_users = db.query(models.User).filter(
        models.User.location == schemas.UserLocation.CHAT_ROOM
    ).all()
    
    # Move all users to the active round
    for user in chat_room_users:
        user.location = schemas.UserLocation.ACTIVE_ROUND
        user.role = schemas.UserRole.PLAYER  # Everyone becomes a player in the round
        user.guess_state = schemas.GuessState.TBD
        user.current_round_id = game_round.id
    
    # Update the round state
    game_round.state = schemas.RoundState.ACTIVE
    
    db.commit()
    db.refresh(game_round)
    
    return game_round

@router.post("/rounds/{round_id}/end", response_model=schemas.Round)
async def end_round(
    round_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    End a round and move all users back to the chat room
    """
    # Get the round
    game_round = db.query(models.Round).filter(models.Round.id == round_id).first()
    if not game_round:
        raise HTTPException(status_code=404, detail="Round not found")
    
    # Ensure the round is active
    if game_round.state != schemas.RoundState.ACTIVE:
        raise HTTPException(status_code=400, detail="Round is not active")
    
    # Get all users in the active round
    active_round_users = db.query(models.User).filter(
        models.User.location == schemas.UserLocation.ACTIVE_ROUND,
        models.User.current_round_id == game_round.id
    ).all()
    
    # Move all users back to the chat room
    for user in active_round_users:
        user.location = schemas.UserLocation.CHAT_ROOM
        user.guess_state = schemas.GuessState.TBD
        user.current_round_id = None
    
    # Update the round state
    game_round.state = schemas.RoundState.INACTIVE
    game_round.end_time = datetime.now()
    
    db.commit()
    db.refresh(game_round)
    
    return game_round

@router.get("/buddies", response_model=List[schemas.Buddy])
async def get_buddies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all buddies
    """
    buddies = db.query(models.Buddy).offset(skip).limit(limit).all()
    
    return buddies

@router.post("/buddies", response_model=schemas.Buddy)
async def create_buddy(
    buddy: schemas.BuddyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new buddy
    """
    # Create the buddy
    db_buddy = models.Buddy(
        name=buddy.name,
        gender=buddy.gender,
        sexual_orientation=buddy.sexual_orientation,
        gender_identity=buddy.gender_identity,
        video_games=buddy.video_games,
        tv_shows=buddy.tv_shows,
        music_artists=buddy.music_artists,
        pet_preference=buddy.pet_preference,
        prompt=buddy.prompt
    )
    db.add(db_buddy)
    db.commit()
    db.refresh(db_buddy)
    
    return db_buddy

@router.post("/guess", response_model=schemas.StandardResponse)
async def make_guess(
    guess: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Make a guess for the secret admirer
    """
    # Ensure the user is in an active round
    if current_user.location != schemas.UserLocation.ACTIVE_ROUND:
        raise HTTPException(status_code=403, detail="Not in an active round")
    
    # Ensure the user hasn't already made a guess
    if current_user.guess_state != schemas.GuessState.TBD:
        raise HTTPException(status_code=400, detail="Already made a guess")
    
    # Get the current round
    game_round = db.query(models.Round).filter(
        models.Round.id == current_user.current_round_id,
        models.Round.state == schemas.RoundState.ACTIVE
    ).first()
    
    if not game_round:
        raise HTTPException(status_code=404, detail="Active round not found")
    
    # Check if the guess is correct
    is_correct = (guess == game_round.secret_admirer)
    
    # Update the user's guess state
    current_user.guess_state = schemas.GuessState.CORRECT if is_correct else schemas.GuessState.INCORRECT
    db.commit()
    
    # Return the result
    return {
        "success": True,
        "message": "Guess recorded",
        "data": {
            "correct": is_correct,
            "secret_admirer": game_round.secret_admirer if not is_correct else None
        }
    }

@router.post("/return-to-lobby", response_model=schemas.StandardResponse)
async def return_to_lobby(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Return to the lobby after making a guess
    """
    # Ensure the user is in an active round
    if current_user.location != schemas.UserLocation.ACTIVE_ROUND:
        raise HTTPException(status_code=403, detail="Not in an active round")
    
    # Move the user back to the chat room
    current_user.location = schemas.UserLocation.CHAT_ROOM
    current_user.guess_state = schemas.GuessState.TBD
    current_user.current_round_id = None
    db.commit()
    
    # Check if there are any users left in the round
    active_users = db.query(models.User).filter(
        models.User.location == schemas.UserLocation.ACTIVE_ROUND,
        models.User.current_round_id == current_user.current_round_id
    ).all()
    
    if not active_users:
        # End the round if no users are left
        game_round = db.query(models.Round).filter(
            models.Round.id == current_user.current_round_id
        ).first()
        
        if game_round:
            game_round.state = schemas.RoundState.INACTIVE
            game_round.end_time = datetime.now()
            db.commit()
    
    return {
        "success": True,
        "message": "Returned to lobby",
        "data": None
    }

@router.post("/conversations/{conversation_id}/message", response_model=schemas.ConversationMessage)
async def send_message_to_buddy(
    conversation_id: int,
    message: schemas.ConversationMessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Send a message to a buddy and get a response
    """
    # Ensure the conversation exists and belongs to the user
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Ensure the user is in an active round
    if current_user.location != schemas.UserLocation.ACTIVE_ROUND:
        raise HTTPException(status_code=403, detail="Not in an active round")
    
    # Create the user message
    db_message = models.ConversationMessage(
        conversation_id=conversation_id,
        sender_type="user",
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