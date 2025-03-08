import logging
import os
from typing import List, Dict, Optional
import re
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import SpinnerColumn, Progress
from services.vector_db import VectorDB
from services.ai_service import AIService

# Optional Azure Translator import
try:
    from azure.cognitiveservices.translation.text import TextTranslationClient
    from msrest.authentication import ApiKeyCredentials
    AZURE_TRANSLATION_AVAILABLE = True
except ImportError:
    AZURE_TRANSLATION_AVAILABLE = False

console = Console()
logger = logging.getLogger(__name__)

class ContextProcessor:
    def __init__(self):
        try:
            self.vector_db = VectorDB()
            self.vector_db.initialize()
            self.ai_service = AIService()
            self.ai_service.initialize()
            logger.info("Successfully initialized services")
        except Exception as e:
            logger.error(f"Error initializing services: {e}")
            self.vector_db = None
            self.ai_service = None
            
        self._welcome_text = """
# 🌟 Welcome to Captain Tractors ChatBot! 🚜

We are India's leading manufacturer of compact and mini tractors, specializing in innovative agricultural solutions since 1982. Our range includes the popular Captain DI-120, DI-3600, and Mini Series tractors, perfect for both agricultural and commercial use.

## How can I assist you today?
- 🚜 Browse our tractor models and specifications
- 📍 Find nearest dealership locations
- 🔧 Schedule service appointments
- 📄 Access product documentation
- 🛠️ Get spare parts information
- 📦 Track your order status

*Type `help` to see all available commands or `clear` to restart our conversation.*
"""
        self.welcome_note = Markdown(self._welcome_text)
        self.setup_translator()
        logging.basicConfig(level=logging.INFO)
        
    def setup_translator(self):
        """Setup Azure Translator if credentials are available"""
        self.translator = None
        if AZURE_TRANSLATION_AVAILABLE:
            try:
                subscription_key = os.getenv('AZURE_TRANSLATOR_KEY')
                endpoint = os.getenv('AZURE_TRANSLATOR_ENDPOINT')
                if subscription_key and endpoint:
                    credentials = ApiKeyCredentials(
                        in_headers={"Ocp-Apim-Subscription-Key": subscription_key}
                    )
                    self.translator = TextTranslationClient(
                        endpoint=endpoint,
                        credentials=credentials
                    )
                    logging.info("Azure Translator initialized successfully")
            except Exception as e:
                logging.warning(f"Failed to initialize Azure Translator: {e}")
                self.translator = None

    def translate_text(self, text: str, target_language: str = 'en') -> str:
        """Translate text if translator is available"""
        if not self.translator:
            return text
        
        try:
            result = self.translator.translate(
                texts=[text],
                target_language=target_language
            )
            if result and len(result) > 0:
                return result[0].translations[0].text
        except Exception as e:
            logging.error(f"Translation error: {e}")
        
        return text

    def show_processing(self):
        with Progress(SpinnerColumn(), transient=True) as progress:
            progress.add_task("Processing...", total=None)

    def start_chat(self) -> str:
        """Return the welcome message"""
        return self._welcome_text

    def clear_chat(self) -> str:
        """Clear chat and return welcome message"""
        return self.start_chat()

    def get_help_text(self) -> str:
        """Return help text"""
        help_text = """
## Available Commands 🔍

**Product Information:**
- `models` - View all tractor models
- `specs [model]` - Get detailed specifications
- `compare [models]` - Compare tractors

**Sales & Support:**
- `dealer [location]` - Find nearest dealership
- `service` - Schedule maintenance
- `parts [model]` - Browse spare parts

**Order Management:**
- `order [number]` - Track your order
- `quote [model]` - Get price quote
- `clear` - Reset conversation

**Language Support:**
- `translate [lang_code]` - Change response language (e.g., 'translate hi' for Hindi)

Need more help? Just ask your question naturally!
"""
        return help_text

    def handle_error(self, error: Exception) -> str:
        error_message = f"""
❗ **Oops!** We encountered an error:
```python
{str(error)}
```
Please try again or contact support@captaintractors.com
"""
        console.print(Markdown(error_message), style="bold red")
        return error_message

    def process_user_input(self, user_input: str) -> str:
        try:
            # Check for empty input
            if not user_input or user_input.strip() == "":
                return ""
                
            # Check for commands
            if user_input.lower().strip() == 'help':
                return self.get_help_text()
            elif user_input.lower().strip() == 'clear':
                return self.clear_chat()
            elif user_input.lower().startswith('translate '):
                lang_code = user_input.split()[1].strip()
                if self.translator:
                    return f"🌐 Translation language set to: {lang_code}"
                else:
                    return "❌ Translation service is not available. Please contact support to enable this feature."
            
            # Process normal chat input
            if not self.ai_service or not self.ai_service.is_available:
                return "I apologize, but the AI service is not properly configured. Please check your GROQ_API_KEY."
                
            # Get relevant context from vector database
            context = []
            if self.vector_db and self.vector_db.is_available:
                # Generate a placeholder vector for the query
                query_vector = self.vector_db._generate_embedding(user_input)
                context = self.vector_db.query_context(query_vector=query_vector, top_k=3)
                logger.info(f"Found {len(context)} context items")
                
            response = self.ai_service.generate_response(user_input, context)
            return response

        except Exception as e:
            logging.error(f"Error processing input: {e}")
            return self.handle_error(e)
            
    def _parse_context_data(self, text: str) -> List[Dict]:
        """Parse the structured text into context chunks"""
        sections = re.split(r'\n\d+\.\s+', text)
        return [{"text": section.strip()} for section in sections if section.strip()]
        
    def process_context_file(self, filename="context_data.txt") -> bool:
        """Process context file and store in vector database"""
        logging.info(f"Processing context file: {filename}")
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                text = file.read()
            
            context_chunks = self._parse_context_data(text)
            
            if not self.vector_db or not self.vector_db.is_available:
                logger.error("Vector database is not available for storing context")
                return False
                
            for chunk in context_chunks:
                self.vector_db.store_context(
                    text=chunk['text'],
                    metadata={
                        'source': 'context_file',
                        'timestamp': str(os.path.getmtime(filename))
                    }
                )
            
            logging.info(f"Successfully processed {len(context_chunks)} context chunks")
            return True
        except Exception as e:
            logging.error(f"Error processing context file: {e}")
            return False
