from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import random
import json
import logging
from datetime import datetime

from app.database.database import get_db, engine
from app.models import models
from app.routers import users, chat, game
from app.utils import active_connections, handle_guess, get_active_round, end_round, check_and_assign_leader

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dream AIM")

# Define allowed origins
allowed_origins = [
    "https://jameshpark.github.io",  # GitHub Pages
    "http://localhost:3000",         # Local development HTTP
    "https://localhost:3000",        # Local development HTTPS
]

# Configure CORS with dynamic origin validation
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https?://[a-zA-Z0-9\-]+\.ngrok(-free)?\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(chat.router)
app.include_router(game.router)

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    await websocket.accept()
    print(f"New connection from user {user_id} with websocket: {websocket}")
    active_connections[user_id] = websocket

    try:
        # Update user status to online and place in chat room
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            await websocket.close(code=1000)
            return

        print(f"Found User {user_id} in the database, moving them to chat room")
        user.location = "CHAT_ROOM"
        db.commit()

        # Check if leader needs to be assigned
        # await check_and_assign_leader(db)
        print(f"Leader checked and assigned")

        # Notify all users about the new connection
        await broadcast_user_status(user_id, "connected")
        print(f"Broadcasted user status to all users")

        while True:
            data = await websocket.receive_text()
            print(f"Received data from user {user_id}: {data}")
            message_data = json.loads(data)
            print(f"Parsed message data: {message_data}")

            # Handle different message types
            if message_data["type"] == "chat_message":
                print(f"Received chat message from user {user_id}: {message_data}")
                await handle_chat_message(user_id, message_data["content"], db)
            elif message_data["type"] == "start_round":
                print(f"Received start round request from user {user_id}: {message_data}")
                # Check if user is leader either by role or by being the only leader in the chat room
                is_leader = user.role == "LEADER"
                print(f"User is leader check 1: {is_leader}")
                if not is_leader:
                    # Check if this user is the leader in the chat room
                    print("***Refreshing leader from start_round websocket handler***")
                    await check_and_assign_leader(db)
                    leader = db.query(models.User).filter(
                        models.User.role == "LEADER",
                        models.User.location == "CHAT_ROOM"
                    ).first()
                    is_leader = leader and leader.id == user.id
                    print(f"User is leader check 2: {is_leader}")

                if is_leader:
                    print(f"User is leader, starting new round")
                    await start_new_round(db, user)
            elif message_data["type"] == "make_guess":
                print(f"Received make guess request from user {user_id}: {message_data}")
                await handle_guess(user_id, message_data["guess"], db)
            elif message_data["type"] == "return_to_lobby":
                print(f"Received return to lobby request from user {user_id}: {message_data}")
                await return_user_to_lobby(user_id, db)

    except WebSocketDisconnect:
        print(f"Disconnected from user {user_id}")

        # Handle disconnection
        if user_id in active_connections:
            del active_connections[user_id]

        # Update user status to offline
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            user.location = "OFFLINE"
            db.commit()

        # Check if leader needs to be reassigned
        print("****Refreshing leader from websocket_endpoint disconnection handler****")
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

async def start_new_round(db: Session, user: models.User):
    """Start a new game round"""
    # Check if there's already an active round
    active_round = get_active_round(db)
    if active_round is not None:
        print(f"Active round {active_round} already exists, skipping new round start")
        return

    # Get all users in the chat room
    chat_room_users = db.query(models.User).filter(models.User.location == "CHAT_ROOM").all()
    print(f"Chat room users: {chat_room_users}")

    if not chat_room_users:
        print(f"No users in the chat room, skipping new round start")
        return

    # Get the leader
    # await check_and_assign_leader(db)
    # leader = db.query(models.User).filter(
    #     models.User.role == "LEADER",
    #     models.User.location == "CHAT_ROOM"
    # ).first()
    # print(f"Leader: {leader}")
    #
    # if not leader:
    #     print(f"No leader found in the chat room, skipping new round start")
    #     return

    # Create a new round using the game router's create_round function
    from app.routers.game import create_round
    from app.schemas.schemas import RoundCreate

    # Create a round with a random secret admirer (1-10)
    round_data = RoundCreate(secret_admirer=random.randint(1, 10))
    new_round = await create_round(round_data, db, user)
    print(f"New round created: {new_round}")

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

async def return_user_to_lobby(user_id: int, db: Session):
    """Return a user to the lobby after they've made their guess"""
    print(f"Returning user {user_id} to the chat room")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.location == "CHAT_ROOM":
        print(f"User {user_id} not found or already in the chat room, skipping return")
        return

    user.location = "CHAT_ROOM"
    user.guess_state = "TBD"
    user.current_round_id = None
    db.commit()

    # Check if there are any users left in the round
    active_users = db.query(models.User).filter(
        models.User.location == "ACTIVE_ROUND",
    ).all()

    if not active_users:
        print(f"No users left in the round, ending round")
        await end_round(db)

    # Notify the user that they've returned to the lobby
    if user_id in active_connections:
        await active_connections[user_id].send_text(json.dumps({
            "type": "returned_to_lobby"
        }))

    # Check if leader needs to be reassigned
    print("****Refreshing leader from return_user_to_lobby****")
    await check_and_assign_leader(db)

@app.get("/")
def read_root():
    return {"message": "Welcome to Dream AIM API"}
