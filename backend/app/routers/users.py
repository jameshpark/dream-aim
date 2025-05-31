from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, UTC
import jwt
from passlib.context import CryptContext
import hashlib

from app.database.database import get_db
from app.models import models
from app.schemas import schemas

# JWT settings
SECRET_KEY = "your-secret-key"  # In production, use a secure secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

PASSPHRASE_HASH = "728739c127665628c61c698d11297879"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# Helper functions
def verify_password(plain_password):
    return hashlib.md5(plain_password.encode()).hexdigest() == PASSPHRASE_HASH

def authenticate_user(db: Session, screen_name: str, password: str):
    user = db.query(models.User).filter(models.User.screen_name == screen_name).first()
    if not user:
        return create_user(schemas.UserCreate(screen_name=screen_name, password=password), db)
    if not verify_password(password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        screen_name: str = payload.get("sub")
        if screen_name is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=screen_name)
    except jwt.PyJWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.screen_name == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

# Routes
@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect passphrase",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.screen_name}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Verify that the provided password is the correct passphrase
    if not verify_password(user.password):
        raise HTTPException(status_code=400, detail="Incorrect passphrase")

    db_user = db.query(models.User).filter(models.User.screen_name == user.screen_name).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Screen name already registered")

    # Store the hash of the fixed passphrase
    db_user = models.User(screen_name=user.screen_name, password=(PASSPHRASE_HASH))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.get("/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")

    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = user.dict(exclude_unset=True)
    if "password" in user_data:
        # Verify that the provided password is the correct passphrase
        if not verify_password(user_data["password"]):
            raise HTTPException(status_code=400, detail="Incorrect passphrase")
        # Store the hash of the fixed passphrase
        user_data["password"] = PASSPHRASE_HASH

    for key, value in user_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/signin", response_model=schemas.Token)
async def signin(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Sign in endpoint specifically for the AOL-style login
    """
    user = authenticate_user(db, user_data.screen_name, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect screen name or passphrase",
        )

    # Update user status to online and in chat room
    user.location = schemas.UserLocation.CHAT_ROOM
    user.last_active = datetime.now()
    db.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.screen_name}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/signout")
async def signout(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Sign out endpoint
    """
    current_user.location = schemas.UserLocation.OFFLINE
    db.commit()
    return {"message": "Successfully signed out"}
