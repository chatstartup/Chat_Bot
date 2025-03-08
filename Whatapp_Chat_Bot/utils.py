import requests
from deep_translator import GoogleTranslator, single_detection
from pinecone import Pinecone
from groq import Groq
import numpy as np
import hashlib
import logging
from config.settings import get_settings
import pinecone
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

class LanguageProcessor:
    def __init__(self):
        self.translator = GoogleTranslator(source='auto', target='en')

    def detect_language(self, text):
        try:
            detection = single_detection(text, api_key=None)
            return detection
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return "en"

    def translate_text(self, text, target_lang="en"):
        try:
            if not text:
                return text
            translator = GoogleTranslator(source='auto', target=target_lang)
            translation = translator.translate(text)
            return translation
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text

class VectorDB:
    """Vector database for storing and retrieving context information"""
    
    def __init__(self):
        """Initialize the vector database"""
        self.api_key = settings.PINECONE_API_KEY
        self.index_name = settings.PINECONE_INDEX
        self.pc = None
        self.index = None
        self.embedding_model = None
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.initialize()
        
    def initialize(self):
        """Initialize the Pinecone client and index"""
        try:
            from pinecone import Pinecone
            from sentence_transformers import SentenceTransformer
            
            # Initialize Pinecone
            self.pc = Pinecone(api_key=self.api_key)
            
            # Check if index exists
            if self.index_name not in self.pc.list_indexes().names():
                logger.warning(f"Index {self.index_name} does not exist. Please run reset_pinecone.py to create it.")
                return False
                
            # Connect to the index
            self.index = self.pc.Index(self.index_name)
            
            # Load embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info(f"Successfully connected to Pinecone index: {self.index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing VectorDB: {str(e)}")
            return False
            
    def embed_text(self, text):
        """Generate embeddings for text
        
        Args:
            text: Text to embed
            
        Returns:
            list: Embedding vector
        """
        if not self.embedding_model:
            logger.error("Embedding model not initialized")
            return None
            
        return self.embedding_model.encode(text).tolist()
        
    def load_context_data(self, context_file="context_data.txt"):
        """Load context data from file and store in vector database
        
        Args:
            context_file: Path to context data file
            
        Returns:
            bool: Success status
        """
        try:
            # Read the context data file
            with open(context_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Split content into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            chunks = text_splitter.split_text(content)
            
            # Create vector records
            records = []
            for i, chunk in enumerate(chunks):
                embedding = self.embed_text(chunk)
                if embedding:
                    records.append({
                        'id': f'chunk_{i}',
                        'values': embedding,
                        'metadata': {'text': chunk}
                    })
            
            # Upsert records to Pinecone
            if records:
                self.index.upsert(vectors=records)
                logger.info(f"Loaded {len(records)} context chunks into vector database")
                return True
            else:
                logger.warning("No valid records created for vector database")
                return False
                
        except Exception as e:
            logger.error(f"Error loading context data: {str(e)}")
            return False
            
    def query(self, query_text, top_k=3):
        """Query the vector database for relevant context
        
        Args:
            query_text: Query text
            top_k: Number of results to return
            
        Returns:
            list: List of relevant context items
        """
        try:
            # Generate query embedding
            query_embedding = self.embed_text(query_text)
            if not query_embedding:
                return []
                
            # Query Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            # Extract and return results
            return [
                {
                    'id': match['id'],
                    'score': match['score'],
                    'text': match['metadata']['text']
                }
                for match in results['matches']
            ]
            
        except Exception as e:
            logger.error(f"Error querying vector database: {str(e)}")
            return []

class AIProcessor:
    def __init__(self):
        try:
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY is not set in environment variables")
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            logger.info("Successfully connected to Groq")
        except Exception as e:
            logger.error(f"Error initializing Groq client: {e}")
            self.client = None

    def generate_response(self, prompt, context=None):
        try:
            if not self.client:
                return "I apologize, but the AI service is not properly configured. Please check your GROQ_API_KEY."

            # Prepare system prompt with company context
            system_prompt = """You are a helpful B2B customer service assistant for Captain Tractors, a company specializing in compact and mini tractors. 
            Be professional, concise, and accurate. Always base your responses on the provided context when available."""

            # Format context for the prompt
            if context:
                # Check if context is a list of items with 'text' or 'content' field
                if isinstance(context, list) and all(isinstance(item, dict) for item in context):
                    context_text = "\n\n".join([
                        f"Context (relevance: {item.get('score', 'N/A')}, source: {item.get('source', 'N/A')}):\n{item.get('text', item.get('content', ''))}"
                        for item in context
                    ])
                    prompt = f"Using the following context, please answer the question:\n\n{context_text}\n\nQuestion: {prompt}\n\nAnswer:"
            
            chat_completion = self.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I apologize, but I'm having trouble processing your request at the moment."
