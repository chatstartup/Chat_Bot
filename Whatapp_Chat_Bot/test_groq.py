import logging
import os
import sys
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
groq_api_key = os.getenv('GROQ_API_KEY')
logger.debug(f"GROQ_API_KEY available: {bool(groq_api_key)}")

try:
    logger.debug("Importing Groq...")
    from groq import Groq
    logger.debug("Successfully imported Groq")
    
    try:
        logger.debug("Initializing Groq client...")
        client = Groq(api_key=groq_api_key)
        logger.debug("Successfully initialized Groq client")
    except Exception as e:
        logger.error(f"Error initializing Groq client: {e}")
except Exception as e:
    logger.error(f"Error importing Groq: {e}")

try:
    logger.debug("Checking if AsyncGroq exists...")
    from groq import AsyncGroq
    logger.debug("Successfully imported AsyncGroq")
    
    try:
        logger.debug("Initializing AsyncGroq client...")
        async_client = AsyncGroq(api_key=groq_api_key)
        logger.debug("Successfully initialized AsyncGroq client")
    except Exception as e:
        logger.error(f"Error initializing AsyncGroq client: {e}")
except ImportError:
    logger.error("AsyncGroq not found in the groq package")
except Exception as e:
    logger.error(f"Other error: {e}")

# Print Python version
logger.debug(f"Python version: {sys.version}")
# Print installed packages
logger.debug("Installed packages:")
try:
    import pkg_resources
    for package in pkg_resources.working_set:
        logger.debug(f"  {package}")
except:
    logger.error("Could not list installed packages")
