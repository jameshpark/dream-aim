from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from .database import engine, Base
from .routers import users, games, chat

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dream AIM")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
app.include_router(users.router)
app.include_router(games.router)
app.include_router(chat.router)

# Mount static files for frontend
# app.mount("/", StaticFiles(directory="frontend/build", html=True), name="frontend")

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
