from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database.database import Base

# Enums for user location, role, and guess state
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

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    screen_name = Column(String, unique=True, index=True)
    password = Column(String)  # In production, store hashed passwords
    location = Column(String, default=UserLocation.OFFLINE)
    role = Column(String, default=UserRole.PLAYER)
    guess_state = Column(String, default=GuessState.TBD)
    current_round_id = Column(Integer, ForeignKey("rounds.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    last_active = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    messages = relationship("Message", back_populates="user")
    current_round = relationship("Round", back_populates="users")
    conversations = relationship("Conversation", back_populates="user")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)

    # Relationships
    user = relationship("User", back_populates="messages")

class Round(Base):
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String, default=RoundState.ACTIVE)
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime, nullable=True)
    secret_admirer = Column(Integer)  # ID of the buddy who is the secret admirer

    # Relationships
    users = relationship("User", back_populates="current_round")
    conversations = relationship("Conversation", back_populates="round")

class Buddy(Base):
    __tablename__ = "buddies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    gender = Column(String)  # male, female, non-binary
    sexual_orientation = Column(String)  # straight, gay, bisexual
    gender_identity = Column(String)  # cis-gender, trans-gender
    video_games = Column(String)  # Comma-separated list of games
    tv_shows = Column(String)  # Comma-separated list of shows
    music_artists = Column(String)  # Comma-separated list of artists
    pet_preference = Column(String)  # cat or dog
    prompt = Column(Text)  # The prompt to use for GPT-4o

    # Relationships
    conversations = relationship("Conversation", back_populates="buddy")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    buddy_id = Column(Integer, ForeignKey("buddies.id"))
    round_id = Column(Integer, ForeignKey("rounds.id"))
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    user = relationship("User", back_populates="conversations")
    buddy = relationship("Buddy", back_populates="conversations")
    round = relationship("Round", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="conversation")

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    sender_type = Column(String)  # "user" or "buddy"
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")