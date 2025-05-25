import logging

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from ..database import get_db
from ..models.models import Game, Boy, User, Guess
from ..schemas.schemas import Game as GameSchema, Boy as BoySchema, Guess as GuessSchema, WaitingRoom, GameState
from ..services.game import game_service
from ..services.websocket import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/games",
    tags=["games"],
    responses={404: {"description": "Not found"}},
)

@router.get("/boys", response_model=List[BoySchema])
async def get_boys(db: Session = Depends(get_db)):
    """Get all boys."""
    boys = db.query(Boy).all()
    return boys

@router.post("/waiting-room/join", response_model=WaitingRoom)
async def join_waiting_room(user_id: int, db: Session = Depends(get_db)):
    """Join the waiting room."""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if a game is in progress
    if game_service.game_in_progress:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A game is already in progress. Please wait for it to end."
        )

    # Join waiting room
    waiting_users = await game_service.join_waiting_room(db, user_id)

    # Get leader (first user in waiting room)
    waiting_user_ids = connection_manager.get_waiting_room_users()

    # If there are no users in the waiting room, set leader_id to None
    if not waiting_user_ids:
        leader_id = None
    else:
        # Get the first user ID from the waiting room list
        leader_id = waiting_user_ids[0]

        # If the user is the only one in the waiting room, make sure they're the leader
        if len(waiting_user_ids) == 1 and waiting_user_ids[0] == user_id:
            leader_id = user_id

    return WaitingRoom(
        users=waiting_users,
        leader_id=leader_id
    )

@router.post("/waiting-room/leave", response_model=WaitingRoom)
async def leave_waiting_room(user_id: int, db: Session = Depends(get_db)):
    """Leave the waiting room."""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Leave waiting room
    waiting_users = await game_service.leave_waiting_room(db, user_id)

    # Get leader (first user in waiting room)
    waiting_user_ids = connection_manager.get_waiting_room_users()

    # If there are no users in the waiting room, set leader_id to None
    if not waiting_user_ids:
        leader_id = None
    else:
        # Get the first user ID from the waiting room list
        leader_id = waiting_user_ids[0]

        # If there's only one user left, make sure they're the leader
        if len(waiting_user_ids) == 1:
            leader_id = waiting_user_ids[0]

    return WaitingRoom(
        users=waiting_users,
        leader_id=leader_id
    )

@router.post("/start", response_model=GameSchema)
async def start_game(leader_id: int, db: Session = Depends(get_db)):
    """Start a new game."""
    # Start the game
    game = await game_service.start_game(db, leader_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to start game. Make sure you are the leader and there are enough users in the waiting room."
        )

    return game

@router.get("/{game_id}", response_model=GameSchema)
async def get_game(game_id: int, db: Session = Depends(get_db)):
    """Get a specific game by ID."""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )

    return game

@router.post("/{game_id}/guess", response_model=GuessSchema)
async def make_guess(game_id: int, user_id: int, boy_id: int, db: Session = Depends(get_db)):
    """Make a guess for the secret admirer."""
    # Make the guess
    guess, is_correct = await game_service.make_guess(db, user_id, game_id, boy_id)
    if not guess:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to make guess. Make sure you are in the game and haven't already guessed."
        )

    return guess

@router.get("/{game_id}/state", response_model=GameState)
async def get_game_state(game_id: int, db: Session = Depends(get_db)):
    """Get the current state of a game."""
    # Get the game
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )

    # Get guesses
    guesses = db.query(Guess).filter(Guess.game_id == game_id).all()

    # Check if there's a winner
    winner_id = None
    for guess in guesses:
        if guess.is_correct:
            winner_id = guess.user_id
            break

    # Check if secret admirer should be revealed
    secret_admirer_revealed = not game.is_active
    secret_admirer_id = game.secret_admirer_id if secret_admirer_revealed else None

    return GameState(
        id=game.id,
        is_active=game.is_active,
        users=game.users,
        leader_id=game.leader_id,
        guesses=guesses,
        winner_id=winner_id,
        secret_admirer_revealed=secret_admirer_revealed,
        secret_admirer_id=secret_admirer_id
    )

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time communication."""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        await websocket.close(code=1008)  # Policy violation
        return

    # Accept the connection
    logger.info(f"*** WebSocket connecting for user {user_id}")
    await connection_manager.connect(websocket, user_id)

    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()

            # Process messages
            try:
                message = json.loads(data)

                # Handle ping messages
                if message.get('type') == 'ping':
                    logger.info(f"Received ping from user {user_id}")
                    # Respond with a pong message
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "data": {}
                    }))
                    logger.info(f"Sent pong to user {user_id}")

                    # Update the active connection in the connection manager
                    # This ensures the connection is still considered active
                    connection_manager.active_connections[user_id] = websocket
            except json.JSONDecodeError:
                logger.error(f"Received invalid JSON from user {user_id}: {data}")
            except Exception as e:
                logger.error(f"Error processing message from user {user_id}: {str(e)}")
    except WebSocketDisconnect:
        # Handle disconnection
        logger.info(f"WebSocket disconnected for user {user_id}")
        connection_manager.disconnect(user_id)
