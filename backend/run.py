import os
import logging
import uvicorn
from dotenv import load_dotenv
from app.init_db import init_db

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Initialize the database
    logger.info("Initializing database...")
    init_db()
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    
    # Run the server
    logger.info(f"Starting server on port {port}...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )