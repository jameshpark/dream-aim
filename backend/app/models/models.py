from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

# Association table for many-to-many relationship between games and users
game_users = Table(
    "game_users",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    games = relationship("Game", secondary=game_users, back_populates="users")
    guesses = relationship("Guess", back_populates="user")
    chats = relationship("Chat", back_populates="user")

class Boy(Base):
    __tablename__ = "boys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    prompt = Column(Text)  # GPT prompt for this boy's personality
    
    # Relationships
    games = relationship("Game", back_populates="secret_admirer")
    chats = relationship("Chat", back_populates="boy")

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    leader_id = Column(Integer, ForeignKey("users.id"))
    secret_admirer_id = Column(Integer, ForeignKey("boys.id"))
    
    # Relationships
    users = relationship("User", secondary=game_users, back_populates="games")
    leader = relationship("User", foreign_keys=[leader_id])
    secret_admirer = relationship("Boy", back_populates="games")
    guesses = relationship("Guess", back_populates="game")
    chats = relationship("Chat", back_populates="game")

class Guess(Base):
    __tablename__ = "guesses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    game_id = Column(Integer, ForeignKey("games.id"))
    boy_id = Column(Integer, ForeignKey("boys.id"))
    is_correct = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="guesses")
    game = relationship("Game", back_populates="guesses")
    boy = relationship("Boy")

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    game_id = Column(Integer, ForeignKey("games.id"))
    boy_id = Column(Integer, ForeignKey("boys.id"))
    message = Column(Text)
    is_from_user = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chats")
    game = relationship("Game", back_populates="chats")
    boy = relationship("Boy", back_populates="chats")