from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

# Boy schemas
class BoyBase(BaseModel):
    name: str
    description: str

class BoyCreate(BoyBase):
    prompt: str

class Boy(BoyBase):
    id: int

    model_config = {
        "from_attributes": True
    }

# Game schemas
class GameBase(BaseModel):
    pass

class GameCreate(GameBase):
    pass

class Game(GameBase):
    id: int
    is_active: bool
    created_at: datetime
    ended_at: Optional[datetime] = None
    leader_id: int
    secret_admirer_id: Optional[int] = None
    users: List[User] = []

    model_config = {
        "from_attributes": True
    }

# Guess schemas
class GuessBase(BaseModel):
    boy_id: int

class GuessCreate(GuessBase):
    pass

class Guess(GuessBase):
    id: int
    user_id: int
    game_id: int
    is_correct: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

# Chat schemas
class ChatBase(BaseModel):
    message: str

class ChatCreate(ChatBase):
    boy_id: int
    game_id: int

class Chat(ChatBase):
    id: int
    user_id: int
    game_id: int
    boy_id: int
    is_from_user: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

# WebSocket message schemas
class WSMessage(BaseModel):
    type: str
    data: dict

# Game state schemas
class WaitingRoom(BaseModel):
    users: List[User]
    leader_id: Optional[int] = None

    model_config = {
        "from_attributes": True
    }

class GameState(BaseModel):
    id: int
    is_active: bool
    users: List[User]
    leader_id: int
    guesses: List[Guess] = []
    winner_id: Optional[int] = None
    secret_admirer_revealed: bool = False
    secret_admirer_id: Optional[int] = None

    model_config = {
        "from_attributes": True
    }
