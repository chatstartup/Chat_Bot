import os
import sys
import logging
import importlib
from dotenv import load_dotenv, find_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check environment variables and .env file"""
    logger.info("=== Checking Environment Setup ===")
    
    # Check for .env file
    env_path = find_dotenv()
    if env_path:
        logger.info(f"Found .env file at: {env_path}")
        load_dotenv(env_path, override=True)
    else:
        logger.warning("No .env file found!")
    
    # Check critical environment variables
    env_vars = {
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
        'PINECONE_API_KEY': os.getenv('PINECONE_API_KEY'),
        'PINECONE_INDEX_NAME': os.getenv('PINECONE_INDEX_NAME'),
        'PINECONE_ENVIRONMENT': os.getenv('PINECONE_ENVIRONMENT')
    }
    
    for name, value in env_vars.items():
        if value:
            masked_value = value[:5] + '*' * (len(value) - 5) if len(value) > 5 else '*****'
            logger.info(f"{name} is set: {masked_value}")
        else:
            logger.error(f"{name} is not set in environment!")
    
    return all(env_vars.values())

def check_imports():
    """Check if all required packages are installed"""
    logger.info("=== Checking Required Packages ===")
    required_packages = [
        'flask', 'groq', 'pinecone', 'dotenv', 
        'pydantic_settings', 'tenacity'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'dotenv':
                # Check for python-dotenv differently
                from dotenv import load_dotenv
                logger.info("Package python-dotenv is installed")
            else:
                importlib.import_module(package)
                logger.info(f"Package {package} is installed")
        except ImportError as e:
            logger.error(f"Package {package} is not installed: {e}")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def check_config():
    """Check if config is working properly"""
    logger.info("=== Checking Configuration ===")
    try:
        from config.settings import get_settings
        settings = get_settings()
        logger.info(f"GROQ_API_KEY from settings: {'present' if settings.GROQ_API_KEY else 'missing'}")
        logger.info(f"PINECONE_API_KEY from settings: {'present' if settings.PINECONE_API_KEY else 'missing'}")
        logger.info(f"PINECONE_INDEX_NAME from settings: {settings.PINECONE_INDEX_NAME}")
        logger.info(f"PINECONE_ENVIRONMENT from settings: {settings.PINECONE_ENVIRONMENT}")
        return bool(settings.GROQ_API_KEY and settings.PINECONE_API_KEY)
    except Exception as e:
        logger.error(f"Error importing or using settings: {e}", exc_info=True)
        return False

def check_ai_service():
    """Check if AI service initializes properly"""
    logger.info("=== Checking AI Service ===")
    try:
        from services.ai_service import AIService
        ai_service = AIService()
        logger.info(f"AI service is_available: {ai_service.is_available}")
        return ai_service.is_available
    except Exception as e:
        logger.error(f"Error initializing AI service: {e}", exc_info=True)
        return False

def check_vector_manager():
    """Check if Vector Manager initializes properly"""
    logger.info("=== Checking Vector Manager ===")
    try:
        from vector_utils import VectorManager
        vector_manager = VectorManager()
        logger.info(f"Vector Manager is_available: {getattr(vector_manager, 'is_available', False)}")
        return getattr(vector_manager, 'is_available', False)
    except Exception as e:
        logger.error(f"Error initializing Vector Manager: {e}", exc_info=True)
        return False

def main():
    """Run all diagnostic checks"""
    logger.info("Starting diagnostics...")
    
    checks = [
        ("Environment Variables", check_environment()),
        ("Required Packages", check_imports()),
        ("Configuration", check_config()),
        ("AI Service", check_ai_service()),
        ("Vector Manager", check_vector_manager())
    ]
    
    # Print summary
    logger.info("\n=== Diagnostic Summary ===")
    all_passed = True
    for name, result in checks:
        status = "PASS" if result else "FAIL"
        if not result:
            all_passed = False
        logger.info(f"{name}: {status}")
    
    if all_passed:
        logger.info("\nAll checks passed! The chatbot should run without errors.")
    else:
        logger.error("\nSome checks failed. Please fix the issues before running the chatbot.")
    
    return all_passed

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
