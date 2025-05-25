import json
from typing import Dict, List, Any
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Map of user_id to WebSocket connection
        self.active_connections: Dict[int, WebSocket] = {}
        # Map of game_id to list of user_ids
        self.game_connections: Dict[int, List[int]] = {}
        # Map of user_id to game_id
        self.user_games: Dict[int, int] = {}
        # Waiting room connections
        self.waiting_room: List[int] = []

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

            # Remove from waiting room if present
            if user_id in self.waiting_room:
                self.waiting_room.remove(user_id)

            # Remove from game if in one
            if user_id in self.user_games:
                game_id = self.user_games[user_id]
                if game_id in self.game_connections and user_id in self.game_connections[game_id]:
                    self.game_connections[game_id].remove(user_id)
                del self.user_games[user_id]

            logger.info(f"User {user_id} disconnected")

    async def send_personal_message(self, message: Dict[str, Any], user_id: int):
        logger.info(f"Active connections: {self.active_connections}")
        logger.info(f"Games: {self.game_connections}")
        logger.info(f"Waiting room: {self.waiting_room}")
        if user_id in self.active_connections:
            try:
                message_json = json.dumps(message)
                logger.info(f"Sending WebSocket message to user {user_id}")
                logger.info(f"WebSocket message type: {message.get('type')}")
                if message.get('type') == 'chat_message' and 'data' in message:
                    data = message['data']
                    logger.info(f"Chat message from {data.get('user', {}).get('username')} to {data.get('boy', {}).get('name')}")
                    logger.info(f"Chat message content: '{data.get('message', '')[:100]}...'")
                    logger.info(f"Is from user: {data.get('is_from_user', False)}")

                await self.active_connections[user_id].send_text(message_json)
                logger.info(f"Successfully sent WebSocket message to user {user_id}")
            except Exception as e:
                logger.error(f"Error sending WebSocket message to user {user_id}: {str(e)}")
        else:
            logger.warning(f"Cannot send message to user {user_id}: not connected")

    async def broadcast_to_waiting_room(self, message: Dict[str, Any]):
        logger.info(f"Broadcasting message to waiting room with {len(self.waiting_room)} users")
        logger.info(f"Broadcast message type: {message.get('type')}")
        for user_id in self.waiting_room:
            await self.send_personal_message(message, user_id)
        logger.info(f"Completed broadcast to waiting room")

    async def broadcast_to_game(self, message: Dict[str, Any], game_id: int):
        if game_id in self.game_connections:
            users = self.game_connections[game_id]
            logger.info(f"Broadcasting message to game {game_id} with {len(users)} users")
            logger.info(f"Broadcast message type: {message.get('type')}")
            for user_id in users:
                await self.send_personal_message(message, user_id)
            logger.info(f"Completed broadcast to game {game_id}")
        else:
            logger.warning(f"Cannot broadcast to game {game_id}: game not found")

    def add_user_to_waiting_room(self, user_id: int):
        if user_id not in self.waiting_room:
            self.waiting_room.append(user_id)
            logger.info(f"User {user_id} added to waiting room")

    def remove_user_from_waiting_room(self, user_id: int):
        if user_id in self.waiting_room:
            self.waiting_room.remove(user_id)
            logger.info(f"User {user_id} removed from waiting room")

    def add_user_to_game(self, user_id: int, game_id: int):
        # Remove from waiting room
        self.remove_user_from_waiting_room(user_id)

        # Add to game
        if game_id not in self.game_connections:
            self.game_connections[game_id] = []
        if user_id not in self.game_connections[game_id]:
            self.game_connections[game_id].append(user_id)

        # Update user's current game
        self.user_games[user_id] = game_id

        logger.info(f"User {user_id} added to game {game_id}")

    def remove_user_from_game(self, user_id: int):
        if user_id in self.user_games:
            game_id = self.user_games[user_id]
            if game_id in self.game_connections and user_id in self.game_connections[game_id]:
                self.game_connections[game_id].remove(user_id)
            del self.user_games[user_id]
            logger.info(f"User {user_id} removed from game {game_id}")

    def get_waiting_room_users(self) -> List[int]:
        return self.waiting_room

    def get_game_users(self, game_id: int) -> List[int]:
        return self.game_connections.get(game_id, [])

    def get_user_game(self, user_id: int) -> int:
        return self.user_games.get(user_id)

# Create a singleton instance
connection_manager = ConnectionManager()
