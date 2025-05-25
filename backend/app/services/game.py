import logging
import random
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.models import User, Boy, Game, Guess, Chat
from ..services.websocket import connection_manager
from ..services.gpt import gpt_service

logger = logging.getLogger(__name__)

class GameService:
    def __init__(self):
        # Cache for active games
        self.active_games: Dict[int, Game] = {}
        # Flag to track if a game is in progress
        self.game_in_progress = False

    async def join_waiting_room(self, db: Session, user_id: int) -> List[User]:
        """Add a user to the waiting room."""
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            return []

        # Add user to waiting room
        connection_manager.add_user_to_waiting_room(user_id)

        # Get all users in waiting room
        waiting_user_ids = connection_manager.get_waiting_room_users()
        waiting_users = db.query(User).filter(User.id.in_(waiting_user_ids)).all()

        # Determine leader ID
        if not waiting_user_ids:
            leader_id = None
        else:
            leader_id = waiting_user_ids[0]

            # If the user is the only one in the waiting room, make sure they're the leader
            if len(waiting_user_ids) == 1 and waiting_user_ids[0] == user_id:
                leader_id = user_id

        # Notify all users in waiting room
        await connection_manager.broadcast_to_waiting_room({
            "type": "waiting_room_update",
            "data": {
                "users": [{"id": user.id, "username": user.username} for user in waiting_users],
                "leader_id": leader_id
            }
        })

        return waiting_users

    async def leave_waiting_room(self, db: Session, user_id: int) -> List[User]:
        """Remove a user from the waiting room."""
        # Remove user from waiting room
        connection_manager.remove_user_from_waiting_room(user_id)

        # Get all users in waiting room
        waiting_user_ids = connection_manager.get_waiting_room_users()
        waiting_users = db.query(User).filter(User.id.in_(waiting_user_ids)).all()

        # Determine leader ID
        if not waiting_user_ids:
            leader_id = None
        else:
            # Get the first user ID from the waiting room list
            leader_id = waiting_user_ids[0]

            # If there's only one user left, make sure they're the leader
            if len(waiting_user_ids) == 1:
                leader_id = waiting_user_ids[0]

        # Notify all users in waiting room
        await connection_manager.broadcast_to_waiting_room({
            "type": "waiting_room_update",
            "data": {
                "users": [{"id": user.id, "username": user.username} for user in waiting_users],
                "leader_id": leader_id
            }
        })

        return waiting_users

    async def start_game(self, db: Session, leader_id: int) -> Optional[Game]:
        """Start a new game with users from the waiting room."""
        # Check if a game is already in progress
        if self.game_in_progress:
            logger.error("Cannot start a new game while one is in progress")
            return None

        # Get all users in waiting room
        waiting_user_ids = connection_manager.get_waiting_room_users()

        # Determine the actual leader ID
        if not waiting_user_ids:
            logger.error("No users in waiting room")
            return None

        # If there's only one user in the waiting room, they should be the leader
        if len(waiting_user_ids) == 1:
            actual_leader_id = waiting_user_ids[0]
        else:
            actual_leader_id = waiting_user_ids[0]

        # Check if the user trying to start the game is the leader
        if leader_id != actual_leader_id:
            logger.error(f"User {leader_id} is not the leader of the waiting room")
            return None

        # Check if there are enough users
        if len(waiting_user_ids) < 1:
            logger.error("Not enough users in waiting room to start a game")
            return None

        # Get all boys
        boys = db.query(Boy).all()
        if not boys:
            logger.error("No boys found in database")
            return None

        # Select a random boy as the secret admirer
        secret_admirer = random.choice(boys)

        # Create a new game
        game = Game(
            is_active=True,
            leader_id=leader_id,
            secret_admirer_id=secret_admirer.id
        )
        db.add(game)
        db.flush()  # Get the game ID

        # Add users to the game
        users = db.query(User).filter(User.id.in_(waiting_user_ids)).all()
        game.users = users

        # Commit to database
        db.commit()
        db.refresh(game)

        # Add game to cache
        self.active_games[game.id] = game

        # Set game in progress flag
        self.game_in_progress = True

        # Add users to game in connection manager
        for user_id in waiting_user_ids:
            connection_manager.add_user_to_game(user_id, game.id)

        # Notify all users in the game
        await connection_manager.broadcast_to_game({
            "type": "game_started",
            "data": {
                "game_id": game.id,
                "users": [{"id": user.id, "username": user.username} for user in users],
                "leader_id": leader_id,
                "boys": [{"id": boy.id, "name": boy.name, "description": boy.description} for boy in boys]
            }
        }, game.id)

        logger.info(f"Game {game.id} started with secret admirer {secret_admirer.id}")

        return game

    async def end_game(self, db: Session, game_id: int, winner_id: Optional[int] = None) -> Game:
        """End a game and reveal the secret admirer."""
        # Get the game
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            logger.error(f"Game {game_id} not found")
            return None

        # Update game
        game.is_active = False
        game.ended_at = datetime.now()

        # Commit to database
        db.commit()
        db.refresh(game)

        # Remove game from cache
        if game_id in self.active_games:
            del self.active_games[game_id]

        # Set game in progress flag
        self.game_in_progress = False

        # Get the secret admirer
        secret_admirer = db.query(Boy).filter(Boy.id == game.secret_admirer_id).first()

        # Notify all users in the game
        await connection_manager.broadcast_to_game({
            "type": "game_ended",
            "data": {
                "game_id": game.id,
                "winner_id": winner_id,
                "secret_admirer": {
                    "id": secret_admirer.id,
                    "name": secret_admirer.name
                }
            }
        }, game.id)

        logger.info(f"Game {game.id} ended with winner {winner_id}")

        return game

    async def make_guess(self, db: Session, user_id: int, game_id: int, boy_id: int) -> Tuple[Guess, bool]:
        """Make a guess for the secret admirer."""
        # Get the game
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game or not game.is_active:
            logger.error(f"Game {game_id} not found or not active")
            return None, False

        # Check if user is in the game
        user_game_id = connection_manager.get_user_game(user_id)
        if user_game_id != game_id:
            logger.error(f"User {user_id} is not in game {game_id}")
            return None, False

        # Check if user already made a guess
        existing_guess = db.query(Guess).filter(
            Guess.user_id == user_id,
            Guess.game_id == game_id
        ).first()
        if existing_guess:
            logger.error(f"User {user_id} already made a guess in game {game_id}")
            return existing_guess, False

        # Check if the boy exists
        boy = db.query(Boy).filter(Boy.id == boy_id).first()
        if not boy:
            logger.error(f"Boy {boy_id} not found")
            return None, False

        # Create the guess
        is_correct = boy_id == game.secret_admirer_id
        guess = Guess(
            user_id=user_id,
            game_id=game_id,
            boy_id=boy_id,
            is_correct=is_correct
        )
        db.add(guess)
        db.commit()
        db.refresh(guess)

        # Check if the guess is correct
        if is_correct:
            # End the game with this user as the winner
            await self.end_game(db, game_id, user_id)
            return guess, True

        # Check if all users have made a guess
        game_user_ids = connection_manager.get_game_users(game_id)
        all_guesses = db.query(Guess).filter(Guess.game_id == game_id).all()

        if len(all_guesses) >= len(game_user_ids):
            # All users have made a guess and none were correct, end the game
            await self.end_game(db, game_id)
        else:
            # Notify all users in the game about the guess
            user = db.query(User).filter(User.id == user_id).first()
            await connection_manager.broadcast_to_game({
                "type": "guess_made",
                "data": {
                    "user": {"id": user.id, "username": user.username},
                    "is_correct": is_correct
                }
            }, game_id)

        return guess, is_correct

    async def send_message(self, db: Session, user_id: int, game_id: int, boy_id: int, message: str) -> Optional[Chat]:
        """Send a message to a boy and get a response."""
        # Log the incoming message
        logger.info(f"Received message from user {user_id} to boy {boy_id} in game {game_id}")
        logger.info(f"Message content: '{message}'")

        # Check if user is in the game
        user_game_id = connection_manager.get_user_game(user_id)
        if user_game_id != game_id:
            logger.error(f"User {user_id} is not in game {game_id}")
            return None

        # Get the game
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game or not game.is_active:
            logger.error(f"Game {game_id} not found or not active")
            return None

        # Check if the boy exists
        boy = db.query(Boy).filter(Boy.id == boy_id).first()
        if not boy:
            logger.error(f"Boy {boy_id} not found")
            return None

        # Create the user message
        user_chat = Chat(
            user_id=user_id,
            game_id=game_id,
            boy_id=boy_id,
            message=message,
            is_from_user=True
        )
        db.add(user_chat)
        db.commit()
        db.refresh(user_chat)
        logger.info(f"Saved user message to database with ID {user_chat.id}")

        # Load the boy's prompt if not already loaded
        if not gpt_service.get_boy_prompt(boy_id):
            logger.info(f"Setting prompt for boy {boy_id}")
            gpt_service.set_boy_prompt(boy_id, boy.prompt)
        else:
            logger.info(f"Using existing prompt for boy {boy_id}")

        # Generate a response from the boy
        logger.info(f"Calling GPT service to generate response from boy {boy_id}")
        response_text = await gpt_service.generate_response(
            user_id=user_id,
            boy_id=boy_id,
            game_id=game_id,
            message=message,
            secret_admirer_id=game.secret_admirer_id
        )
        logger.info(f"Received response from GPT service: '{response_text[:100]}...'")

        # Create the boy's response
        boy_chat = Chat(
            user_id=user_id,
            game_id=game_id,
            boy_id=boy_id,
            message=response_text,
            is_from_user=False
        )
        db.add(boy_chat)
        db.commit()
        db.refresh(boy_chat)
        logger.info(f"Saved boy response to database with ID {boy_chat.id}")

        # Send the response to the user
        user = db.query(User).filter(User.id == user_id).first()
        message_data = {
            "type": "chat_message",
            "data": {
                "id": boy_chat.id,
                "user": {"id": user.id, "username": user.username},
                "boy": {"id": boy.id, "name": boy.name},
                "message": response_text,
                "is_from_user": False,
                "created_at": boy_chat.created_at.isoformat()
            }
        }
        logger.info(f"Sending response to user {user_id} via WebSocket")
        logger.info(f"WebSocket message type: {message_data['type']}")
        logger.info(f"WebSocket message data: {message_data['data']}")

        await connection_manager.send_personal_message(message_data, user_id)
        logger.info(f"Response sent to user {user_id}")

        return boy_chat

# Create a singleton instance
game_service = GameService()
