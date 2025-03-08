import os
import sys
import logging
from dotenv import find_dotenv, load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    # Print current working directory
    cwd = os.getcwd()
    logger.info(f"Current working directory: {cwd}")
    
    # Print where Python is looking for modules
    logger.info("Python path:")
    for p in sys.path:
        logger.info(f"  {p}")
    
    # Find .env file
    env_path = find_dotenv()
    if env_path:
        logger.info(f"Found .env file at: {env_path}")
        # Load .env file
        load_dotenv(env_path)
        # Check if GROQ_API_KEY is loaded
        groq_key = os.getenv('GROQ_API_KEY')
        logger.info(f"GROQ_API_KEY loaded: {bool(groq_key)}")
        if groq_key:
            # Print first 5 chars of the key for verification
            logger.info(f"GROQ_API_KEY starts with: {groq_key[:5]}")
    else:
        logger.error("No .env file found!")
        
    # Print all environment variables starting with GROQ or PINECONE
    logger.info("Environment variables:")
    for key, value in os.environ.items():
        if key.startswith('GROQ') or key.startswith('PINECONE'):
            # Only print first 5 chars of the value for security
            if value:
                value_preview = value[:5] + "..." if len(value) > 5 else value
            else:
                value_preview = "(empty)"
            logger.info(f"  {key}: {value_preview}")

if __name__ == "__main__":
    main()
