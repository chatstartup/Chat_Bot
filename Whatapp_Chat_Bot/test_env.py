import os
import logging
from dotenv import load_dotenv, find_dotenv
from config.settings import get_settings

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Try to load .env file directly
    env_path = find_dotenv()
    if env_path:
        logger.info(f"Found .env file at: {env_path}")
        load_dotenv(env_path, override=True)
        logger.info(f"Loaded .env file from: {env_path}")
    else:
        logger.warning("No .env file found!")
    
    # Check if environment variables are loaded
    groq_key = os.getenv('GROQ_API_KEY', '')
    pinecone_key = os.getenv('PINECONE_API_KEY', '')
    logger.info(f"Direct os.getenv - GROQ_API_KEY present: {bool(groq_key)}")
    logger.info(f"Direct os.getenv - PINECONE_API_KEY present: {bool(pinecone_key)}")
    
    # Get values from settings
    settings = get_settings()
    logger.info(f"From settings - GROQ_API_KEY present: {bool(settings.GROQ_API_KEY)}")
    logger.info(f"From settings - PINECONE_API_KEY present: {bool(settings.PINECONE_API_KEY)}")
    
    # Debug actual values (be careful with showing API keys in logs)
    logger.info(f"GROQ_API_KEY first 5 chars: {groq_key[:5] if groq_key else 'empty'}")
    logger.info(f"PINECONE_API_KEY first 5 chars: {pinecone_key[:5] if pinecone_key else 'empty'}")

if __name__ == "__main__":
    main()
