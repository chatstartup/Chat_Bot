"""
Reset Pinecone Index Script

This script deletes and recreates the Pinecone index for the WhatsApp Chat Bot.
It also loads the context data from context_data.txt into the vector database.
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from config.settings import get_settings
from utils import VectorDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
settings = get_settings()

class PineconeManager:
    """Manages Pinecone index operations"""
    
    def __init__(self):
        """Initialize the Pinecone manager"""
        self.api_key = settings.PINECONE_API_KEY
        self.index_name = settings.PINECONE_INDEX
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2 model
        self.pc = Pinecone(api_key=self.api_key)
        
    def reset_index(self):
        """Reset the Pinecone index by deleting and recreating it"""
        try:
            # Check if index exists
            logger.info(f"Initialized Pinecone with API key: {self.api_key[:5]}***")
            
            # Delete index if it exists
            if self.index_name in self.pc.list_indexes().names():
                logger.info(f"Deleting existing index: {self.index_name}")
                self.pc.delete_index(self.index_name)
                # Wait for deletion to complete
                time.sleep(5)
            
            # Create new index
            logger.info(f"Creating new index: {self.index_name} with dimension {self.dimension}")
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            
            # Wait for index to be ready
            logger.info("Waiting for index to be ready...")
            time.sleep(10)
            
            # Verify index was created
            if self.index_name in self.pc.list_indexes().names():
                logger.info(f"Successfully created index: {self.index_name}")
                return True
            else:
                logger.error(f"Failed to create index: {self.index_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error resetting Pinecone index: {str(e)}")
            return False
            
    def load_context_data(self):
        """Load context data into the vector database"""
        try:
            # Initialize VectorDB
            vector_db = VectorDB()
            
            # Load context data
            logger.info("Loading context data into vector database...")
            success = vector_db.load_context_data()
            
            if success:
                logger.info("Successfully loaded context data into vector database")
                return True
            else:
                logger.error("Failed to load context data into vector database")
                return False
                
        except Exception as e:
            logger.error(f"Error loading context data: {str(e)}")
            return False

def main():
    """Main function to reset Pinecone index and load context data"""
    logger.info("Starting Pinecone reset process")
    
    # Check if API key is available
    if not settings.PINECONE_API_KEY:
        logger.error("Pinecone API key not found in environment variables")
        return False
        
    # Check if index name is available
    if not settings.PINECONE_INDEX:
        logger.error("Pinecone index name not found in environment variables")
        return False
        
    # Reset Pinecone index
    manager = PineconeManager()
    reset_success = manager.reset_index()
    
    if not reset_success:
        logger.error("Failed to reset Pinecone index")
        return False
        
    # Load context data
    load_success = manager.load_context_data()
    
    if not load_success:
        logger.error("Failed to load context data")
        return False
        
    logger.info("Pinecone reset process completed successfully")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
