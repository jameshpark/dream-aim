from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import asyncio
import random
import json
import logging
from datetime import datetime

from app.database.database import get_db, engine
from app.models import models
from app.schemas import schemas
from app.routers import users, chat, game

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dream AIM")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(chat.router)
app.include_router(game.router)

# WebSocket connections
active_connections: Dict[int, WebSocket] = {}
active_round: Optional[int] = None

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    await websocket.accept()
    active_connections[user_id] = websocket
    
    try:
        # Update user status to online and place in chat room
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            await websocket.close(code=1000)
            return
        
        user.location = "CHAT_ROOM"
        db.commit()
        
        # Check if leader needs to be assigned
        await check_and_assign_leader(db)
        
        # Notify all users about the new connection
        await broadcast_user_status(user_id, "connected")
        
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            if message_data["type"] == "chat_message":
                await handle_chat_message(user_id, message_data["content"], db)
            elif message_data["type"] == "start_round" and user.role == "LEADER":
                await start_new_round(db)
            elif message_data["type"] == "make_guess":
                await handle_guess(user_id, message_data["guess"], db)
            elif message_data["type"] == "return_to_lobby":
                await return_user_to_lobby(user_id, db)
    
    except WebSocketDisconnect:
        # Handle disconnection
        if user_id in active_connections:
            del active_connections[user_id]
        
        # Update user status to offline
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            user.location = "OFFLINE"
            db.commit()
        
        # Check if leader needs to be reassigned
        await check_and_assign_leader(db)
        
        # Notify all users about the disconnection
        await broadcast_user_status(user_id, "disconnected")

async def broadcast_user_status(user_id: int, status: str):
    """Broadcast user connection/disconnection status to all connected users"""
    for connection_id, connection in active_connections.items():
        await connection.send_text(json.dumps({
            "type": "user_status",
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }))

async def handle_chat_message(user_id: int, content: str, db: Session):
    """Handle and broadcast chat messages"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return
    
    # Create message in database
    new_message = models.Message(
        user_id=user_id,
        content=content,
        timestamp=datetime.now()
    )
    db.add(new_message)
    db.commit()
    
    # Broadcast message to all users in the same location
    for connection_id, connection in active_connections.items():
        target_user = db.query(models.User).filter(models.User.id == connection_id).first()
        if target_user and target_user.location == user.location:
            await connection.send_text(json.dumps({
                "type": "chat_message",
                "user_id": user_id,
                "username": user.screen_name,
                "content": content,
                "timestamp": new_message.timestamp.isoformat()
            }))

async def check_and_assign_leader(db: Session):
    """Check if a leader needs to be assigned in the chat room"""
    # Get all users in the chat room
    chat_room_users = db.query(models.User).filter(models.User.location == "CHAT_ROOM").all()
    
    if not chat_room_users:
        return
    
    # Check if any user is already a leader
    leader_exists = any(user.role == "LEADER" for user in chat_room_users)
    
    if not leader_exists:
        # Randomly select a leader
        new_leader = random.choice(chat_room_users)
        new_leader.role = "LEADER"
        
        # Make sure all other users are players
        for user in chat_room_users:
            if user.id != new_leader.id:
                user.role = "PLAYER"
        
        db.commit()
        
        # Notify all users about the new leader
        for connection_id, connection in active_connections.items():
            await connection.send_text(json.dumps({
                "type": "leader_assigned",
                "leader_id": new_leader.id,
                "leader_name": new_leader.screen_name
            }))

async def start_new_round(db: Session):
    """Start a new game round"""
    global active_round
    
    # Check if there's already an active round
    if active_round is not None:
        return
    
    # Get all users in the chat room
    chat_room_users = db.query(models.User).filter(models.User.location == "CHAT_ROOM").all()
    
    if not chat_room_users:
        return
    
    # Create a new round
    new_round = models.Round(
        state="ACTIVE",
        start_time=datetime.now(),
        secret_admirer=random.randint(1, 10)  # Randomly select a secret admirer from the 10 buddies
    )
    db.add(new_round)
    db.commit()
    
    active_round = new_round.id
    
    # Move all users to the active round
    for user in chat_room_users:
        user.location = "ACTIVE_ROUND"
        user.role = "PLAYER"  # Everyone becomes a player in the round
        user.guess_state = "TBD"
        user.current_round_id = new_round.id
        
    db.commit()
    
    # Notify all users about the new round
    for user in chat_room_users:
        if user.id in active_connections:
            await active_connections[user.id].send_text(json.dumps({
                "type": "round_started",
                "round_id": new_round.id,
                "timestamp": new_round.start_time.isoformat()
            }))

async def handle_guess(user_id: int, guess: int, db: Session):
    """Handle a user's guess"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.location != "ACTIVE_ROUND" or not active_round:
        return
    
    # Get the current round
    round = db.query(models.Round).filter(models.Round.id == active_round).first()
    if not round or round.state != "ACTIVE":
        return
    
    # Check if the guess is correct
    is_correct = (guess == round.secret_admirer)
    user.guess_state = "CORRECT" if is_correct else "INCORRECT"
    db.commit()
    
    # Notify the user about their guess result
    if user_id in active_connections:
        await active_connections[user_id].send_text(json.dumps({
            "type": "guess_result",
            "correct": is_correct,
            "secret_admirer": round.secret_admirer if not is_correct else None
        }))
    
    # Check if all users have made their guesses
    active_users = db.query(models.User).filter(
        models.User.location == "ACTIVE_ROUND",
        models.User.current_round_id == active_round
    ).all()
    
    users_with_guesses = db.query(models.User).filter(
        models.User.location == "ACTIVE_ROUND",
        models.User.current_round_id == active_round,
        models.User.guess_state != "TBD"
    ).all()
    
    if len(active_users) > 0 and len(active_users) == len(users_with_guesses):
        # All users have made their guesses, schedule round end
        asyncio.create_task(end_round_after_delay(db))

async def return_user_to_lobby(user_id: int, db: Session):
    """Return a user to the lobby after they've made their guess"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.location != "ACTIVE_ROUND":
        return
    
    user.location = "CHAT_ROOM"
    user.guess_state = "TBD"
    user.current_round_id = None
    db.commit()
    
    # Check if there are any users left in the round
    active_users = db.query(models.User).filter(
        models.User.location == "ACTIVE_ROUND",
        models.User.current_round_id == active_round
    ).all()
    
    if not active_users:
        await end_round(db)
    
    # Notify the user that they've returned to the lobby
    if user_id in active_connections:
        await active_connections[user_id].send_text(json.dumps({
            "type": "returned_to_lobby"
        }))
    
    # Check if leader needs to be reassigned
    await check_and_assign_leader(db)

async def end_round_after_delay(db: Session):
    """End the round after a 10-second delay"""
    await asyncio.sleep(10)
    await end_round(db)

async def end_round(db: Session):
    """End the current round and return all users to the lobby"""
    global active_round
    
    if not active_round:
        return
    
    # Get the current round
    round = db.query(models.Round).filter(models.Round.id == active_round).first()
    if not round:
        active_round = None
        return
    
    # Mark the round as inactive
    round.state = "INACTIVE"
    round.end_time = datetime.now()
    
    # Return all users to the lobby
    active_users = db.query(models.User).filter(
        models.User.location == "ACTIVE_ROUND",
        models.User.current_round_id == round.id
    ).all()
    
    for user in active_users:
        user.location = "CHAT_ROOM"
        user.guess_state = "TBD"
        user.current_round_id = None
    
    db.commit()
    active_round = None
    
    # Notify all users that the round has ended
    for user in active_users:
        if user.id in active_connections:
            await active_connections[user.id].send_text(json.dumps({
                "type": "round_ended",
                "round_id": round.id
            }))
    
    # Check if leader needs to be reassigned
    await check_and_assign_leader(db)

@app.get("/")
def read_root():
    return {"message": "Welcome to Dream AIM API"}