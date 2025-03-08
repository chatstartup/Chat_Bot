from pinecone import Pinecone, ServerlessSpec
from config.settings import get_settings

settings = get_settings()

def setup_pinecone():
    try:
        print("Initializing Pinecone...")
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        
        # Check if index exists
        indexes = pc.list_indexes()
        print(f"Existing indexes: {indexes}")
        
        if settings.PINECONE_INDEX_NAME not in [index.name for index in indexes]:
            print(f"Creating new index: {settings.PINECONE_INDEX_NAME}")
            
            # Create serverless index in us-east-1 (free tier)
            spec = ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
            
            pc.create_index(
                name=settings.PINECONE_INDEX_NAME,
                dimension=384,  # Aligned with existing index
                metric="cosine",
                spec=spec
            )
            print("Index created successfully")
        else:
            print(f"Index {settings.PINECONE_INDEX_NAME} already exists")
        
        # Describe the index
        index = pc.Index(settings.PINECONE_INDEX_NAME)
        description = index.describe_index_stats()
        print(f"\nIndex statistics: {description}")
        
        return True
    
    except Exception as e:
        print(f"Error setting up Pinecone: {e}")
        return False

if __name__ == "__main__":
    setup_pinecone()
