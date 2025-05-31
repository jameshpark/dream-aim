# Dream AIM

A web application that emulates the board game "Electronic Dream Phone" with an AOL Instant Messenger UI/UX.

## Overview

This application allows multiple players (up to 50) to play a game where they try to identify their secret admirer through conversations with potential admirers. The UI is designed to look like AOL Instant Messenger from the early 2000s.

## Features

- AOL Instant Messenger-style UI
- Multiplayer support (up to 50 players)
- Real-time chat functionality
- Game rounds with buddy conversations
- Integration with OpenAI's GPT-4o for buddy conversations
- Responsive design for both mobile and desktop

## Tech Stack

- **Frontend**: React
- **Backend**: Python (FastAPI)
- **Database**: PostgreSQL
- **AI**: OpenAI GPT-4o

## Setup

### Prerequisites

- Python 3.10+
- Node.js 14+
- PostgreSQL
- OpenAI API key

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Install pipenv if you don't have it:
   ```
   pip install pipenv
   ```

3. Install dependencies using pipenv:
   ```
   pipenv install
   ```

4. Activate the pipenv shell:
   ```
   pipenv shell
   ```

5. Set up environment variables:
   Create a `.env` file in the backend directory with the following variables:
   ```
   DATABASE_URL=postgresql://username:password@localhost/dream_aim
   OPENAI_API_KEY=your_openai_api_key
   SECRET_KEY=your_secret_key_for_jwt
   ```

6. Initialize the database:
   ```
   pipenv run python -m app.init_db
   ```

   Or if you're already in the pipenv shell:
   ```
   python -m app.init_db
   ```

7. Run the backend server:
   ```
   pipenv run python run.py
   ```

   Or if you're already in the pipenv shell:
   ```
   python run.py
   ```

   Alternatively, you can use uvicorn directly:
   ```
   pipenv run uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Create a `.env` file in the frontend directory with the following variables:
   ```
   REACT_APP_API_URL=http://localhost:8000
   ```

4. Run the frontend development server:
   ```
   npm start
   ```

## Game Flow

1. User signs on with a screen name and password
2. User is placed in a chat room with other users
3. One user is designated as the "Leader" who can start a new round
4. When a round starts, users are presented with a buddy list of potential secret admirers
5. Users can chat with buddies to gather clues
6. Users make a guess about who their secret admirer is
7. After all users have made their guesses or the round times out, users return to the chat room
8. The process repeats

## License

MIT
