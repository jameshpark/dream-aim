# Dream AIM

Dream AIM is a web application that emulates the board game Dream Phone but with an AOL Instant Messenger (AIM) like user interface. Players chat with virtual boys to gather clues about which one is their secret admirer, then compete to be the first to guess correctly.

## Features

- AOL Instant Messenger-like user interface
- Real-time chat with AI-powered boys using GPT-4o
- Multiplayer gameplay with waiting room
- Leader-based game start system
- Guessing mechanism to identify the secret admirer
- Round-based gameplay

## Tech Stack

### Backend
- FastAPI (Python web framework)
- SQLAlchemy (ORM)
- PostgreSQL (Database)
- WebSockets (Real-time communication)
- OpenAI GPT-4o API (AI chat)

### Frontend
- React
- React Router
- Axios
- WebSocket API
- Styled Components

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 14+
- PostgreSQL (or Docker and Docker Compose if using containerized database)

### Backend Setup

1. Clone the repository:
```
git clone https://github.com/yourusername/dream-aim.git
cd dream-aim
```

2. Create a virtual environment and install dependencies:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file in the backend directory (copy from `.env.example`):
```
# Database configuration
DATABASE_URL=postgresql://postgres:postgres@localhost/dreamaim

# OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here

# Server configuration
PORT=8000
```

4. Create a PostgreSQL database:

   Option A: Using local PostgreSQL installation:
   ```
   createdb dreamaim
   ```

   Option B: Using Docker (recommended):
   ```
   docker-compose up -d
   ```
   This will start a PostgreSQL container with the correct configuration.

5. Run the backend server:
```
cd backend
python run.py
```

### Frontend Setup

1. Install dependencies:
```
cd frontend
npm install
```

2. Start the development server:
```
npm start
```

## How to Play

1. **Login**: Enter a username to join the game.

2. **Waiting Room**: Wait for other players to join. The first player to join becomes the leader and can start the game when ready.

3. **Game**: Once the game starts, you'll see a buddy list with all the boys.
   - Click on a boy to start chatting with them
   - Ask questions to gather clues about who the secret admirer might be
   - Each boy will give hints about what the secret admirer is or isn't wearing, doing, etc.
   - When you think you know who the secret admirer is, click "Make a Guess" and select a boy

4. **Winning**: The first player to correctly guess the secret admirer wins the round.
   - Each player gets one guess per round
   - If all players guess incorrectly, the secret admirer is revealed and the round ends

5. **Next Round**: After a round ends, players can join the waiting room for the next round.

## Development

### Backend Structure
- `backend/app/main.py`: Main FastAPI application
- `backend/app/database.py`: Database configuration
- `backend/app/models/`: Database models
- `backend/app/schemas/`: Pydantic schemas
- `backend/app/routers/`: API endpoints
- `backend/app/services/`: Business logic
- `backend/app/init_db.py`: Database initialization script

### Frontend Structure
- `frontend/src/App.js`: Main React component
- `frontend/src/pages/`: Page components
- `frontend/src/components/`: Reusable components
- `frontend/src/styles/`: CSS styles
- `frontend/src/utils/`: Utility functions
- `frontend/src/context/`: React context providers

## License

MIT
