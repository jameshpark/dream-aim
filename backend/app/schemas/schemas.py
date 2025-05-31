from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import enum

# Enums
class UserLocation(str, enum.Enum):
    OFFLINE = "OFFLINE"
    CHAT_ROOM = "CHAT_ROOM"
    ACTIVE_ROUND = "ACTIVE_ROUND"

class UserRole(str, enum.Enum):
    LEADER = "LEADER"
    PLAYER = "PLAYER"

class GuessState(str, enum.Enum):
    TBD = "TBD"
    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"

class RoundState(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

# User schemas
class UserBase(BaseModel):
    screen_name: str

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class UserUpdate(BaseModel):
    screen_name: Optional[str] = None
    password: Optional[str] = None
    location: Optional[UserLocation] = None
    role: Optional[UserRole] = None
    guess_state: Optional[GuessState] = None
    current_round_id: Optional[int] = None

class UserInDB(UserBase):
    id: int
    location: UserLocation
    role: UserRole
    guess_state: GuessState
    current_round_id: Optional[int] = None
    created_at: datetime
    last_active: datetime

    class Config:
        orm_mode = True

class User(UserInDB):
    pass

# Message schemas
class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    user_id: int

class Message(MessageBase):
    id: int
    user_id: int
    timestamp: datetime
    user: User

    class Config:
        orm_mode = True

# Round schemas
class RoundBase(BaseModel):
    state: RoundState = RoundState.ACTIVE

class RoundCreate(RoundBase):
    secret_admirer: int

class Round(RoundBase):
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    secret_admirer: int
    users: List[User] = []

    class Config:
        orm_mode = True

# Buddy schemas
class BuddyBase(BaseModel):
    name: str
    gender: str
    sexual_orientation: str
    gender_identity: str
    video_games: str
    tv_shows: str
    music_artists: str
    pet_preference: str
    prompt: str

class BuddyCreate(BuddyBase):
    pass

class Buddy(BuddyBase):
    id: int

    class Config:
        orm_mode = True

# Conversation schemas
class ConversationBase(BaseModel):
    user_id: int
    buddy_id: int
    round_id: int

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: int
    created_at: datetime
    messages: List[Any] = []

    class Config:
        orm_mode = True

# Conversation message schemas
class ConversationMessageBase(BaseModel):
    content: str
    sender_type: str  # "user" or "buddy"

class ConversationMessageCreate(ConversationMessageBase):
    conversation_id: int

class ConversationMessage(ConversationMessageBase):
    id: int
    conversation_id: int
    timestamp: datetime

    class Config:
        orm_mode = True

# Update Conversation to use ConversationMessage
Conversation.update_forward_refs()

# Token schema for authentication
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# WebSocket message schemas
class WebSocketMessage(BaseModel):
    type: str
    content: Optional[Dict[str, Any]] = None

# Response schemas
class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None