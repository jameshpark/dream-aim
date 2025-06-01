import asyncio
import json
import random
from datetime import datetime
from typing import Dict

from sqlalchemy.orm import Session
from starlette.websockets import WebSocket

from app.models import models
from app.schemas.schemas import RoundState

# WebSocket connections
active_connections: Dict[int, WebSocket] = {}


async def handle_guess(user_id: int, guess: int, db: Session):
    """Handle a user's guess"""
    game_round = get_active_round(db)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.location != "ACTIVE_ROUND" or not game_round:
        return

    # Get the current round
    if not game_round or game_round.state != "ACTIVE":
        return

    # Check if the guess is correct
    is_correct = (guess == game_round.secret_admirer)
    user.guess_state = "CORRECT" if is_correct else "INCORRECT"
    db.commit()

    # Notify the user about their guess result
    actual_secret_admirer = db.query(models.Buddy).filter(
        models.Buddy.id == game_round.secret_admirer
    ).first()

    if user_id in active_connections:
        await active_connections[user_id].send_text(json.dumps({
            "type": "guess_result",
            "correct": is_correct,
            "secret_admirer": actual_secret_admirer.name
        }))

    # Check if all users have made their guesses
    active_users = db.query(models.User).filter(
        models.User.location == "ACTIVE_ROUND",
        models.User.current_round_id == game_round.id,
    ).all()

    users_with_guesses = db.query(models.User).filter(
        models.User.location == "ACTIVE_ROUND",
        models.User.current_round_id == game_round.id,
        models.User.guess_state != "TBD"
    ).all()

    if len(active_users) > 0 and len(active_users) == len(users_with_guesses):
        # All users have made their guesses, schedule round end
        asyncio.create_task(end_round_after_delay(game_round.id, db))

    return {
        "correct": is_correct,
        "secret_admirer": actual_secret_admirer.name
    }


def get_active_round(db: Session):
    return db.query(models.Round).filter(models.Round.state == RoundState.ACTIVE).first()


async def end_round_after_delay(game_round_id: int, db: Session):
    """End the round after a 10-second delay"""
    await asyncio.sleep(10)
    await end_round(game_round_id, db)


async def end_round(game_round_id: int, db: Session):
    """End the current round and return all users to the lobby"""
    game_round = db.query(models.Round).filter(models.Round.id == game_round_id).first()

    # Get the current round
    if not game_round:
        return

    # Mark the round as inactive
    if game_round.state == "INACTIVE":
        # already marked inactive, skip
        return

    game_round.state = "INACTIVE"
    game_round.end_time = datetime.now()

    # Return all users to the lobby
    active_users = db.query(models.User).filter(
        models.User.location == "ACTIVE_ROUND",
        models.User.current_round_id == game_round.id
    ).all()

    for user in active_users:
        user.location = "CHAT_ROOM"
        user.guess_state = "TBD"
        user.current_round_id = None

    db.commit()

    # Notify all users that the round has ended
    for user in active_users:
        if user.id in active_connections:
            await active_connections[user.id].send_text(json.dumps({
                "type": "round_ended",
                "round_id": game_round.id
            }))

    # Check if leader needs to be reassigned
    print("****Refreshing leader from end_round****")
    await check_and_assign_leader(db)


async def check_and_assign_leader(db: Session):
    """Check if a leader needs to be assigned in the chat room"""
    # Get all users in the chat room
    print("Refreshing chat room leader")
    chat_room_users = db.query(models.User).filter(models.User.location == "CHAT_ROOM").all()

    if not chat_room_users:
        print("No users in the chat room, skipping leader refresh")
        return

    # Check if any user is already a leader
    current_leader = db.query(models.User).filter(
        models.User.role == "LEADER",
        models.User.location == "CHAT_ROOM"
    ).first()

    if current_leader:
        # Leader exists and is in the chat room, no need to reassign
        print("Leader already exists in the chat room, skipping leader refresh")
        return

    # No leader in chat room or offline leader is inactive for too long, assign a new one
    print("No leader in chat room or offline leader is inactive for too long, assigning a new one...")
    new_leader = random.choice(chat_room_users)
    new_leader.role = "LEADER"
    print(f"New leader selected: {new_leader}")

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
