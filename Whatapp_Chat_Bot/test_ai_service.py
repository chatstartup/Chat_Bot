import logging
import asyncio
from services.ai_service import AIService
from config.settings import get_settings

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
settings = get_settings()

async def main():
    # Initialize AI service
    logger.info("Creating AIService...")
    ai_service = AIService()
    
    # Check if service is available
    if ai_service.is_available:
        logger.info("AI service is available!")
        
        # Test with simple prompt
        logger.info("Testing with simple prompt...")
        response = await ai_service.generate_response("Hello, how are you today?")
        logger.info(f"Response: {response}")
    else:
        logger.error("AI service is not available. Check your API key.")

if __name__ == "__main__":
    asyncio.run(main())
