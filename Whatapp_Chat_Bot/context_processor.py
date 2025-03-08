import logging
import os
from typing import List, Dict, Optional, Any
import re
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import SpinnerColumn, Progress
from services.vector_db import VectorDB
from services.ai_service import AIService
from config.settings import get_settings
from fuzzywuzzy import fuzz

settings = get_settings()

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
    def __init__(self, vector_db=None, ai_service=None):
        try:
            # Use provided services if available, otherwise initialize them
            if vector_db:
                self.vector_db = vector_db
                logger.info("Using provided VectorDB")
            else:
                logger.debug("Initializing VectorDB")
                self.vector_db = VectorDB()
                self.vector_db.initialize()
                
            # Don't initialize AIService here to avoid circular dependency
            self.ai_service = ai_service
            logger.info("Successfully initialized context processor")
        except Exception as e:
            logger.error(f"Error initializing services: {e}")
            self.vector_db = None
            self.ai_service = None
            
        self._welcome_text = """
# 🌟 Welcome to Captain Tractors! 🚜

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
        self.contexts = self._load_contexts()

    def _load_contexts(self):
        """Load context definitions from file"""
        contexts = {}
        current_context = {}
        
        try:
            with open('context_data.txt', 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                        
                    if line.startswith('[') and line.endswith(']'):
                        context_name = line[1:-1]
                        current_context = {
                            'name': context_name,
                            'actions': [],
                            'triggers': []
                        }
                        contexts[context_name] = current_context
                    elif '=' in line:
                        key, value = map(str.strip, line.split('=', 1))
                        if key == 'triggers':
                            current_context['triggers'] = [t.strip() for t in value.split(',')]
                        elif key == 'actions':
                            current_context['actions'] = [a.strip() for a in value.split(',')]
                        else:
                            current_context[key] = value
            
            # Ensure we have at least a General context
            if 'General' not in contexts:
                contexts['General'] = {
                    'name': 'General',
                    'description': 'Default conversational mode',
                    'triggers': ['*'],
                    'actions': ['maintain_conversation']
                }
                
            logger.info(f"Loaded {len(contexts)} contexts from context_data.txt")
            return contexts
        except Exception as e:
            logger.error(f"Error loading contexts: {e}")
            # Return a default context if file loading fails
            return {
                'General': {
                    'name': 'General',
                    'description': 'Default conversational mode',
                    'triggers': ['*'],
                    'actions': ['maintain_conversation']
                }
            }

    def process_context(self, message):
        """Process message to determine context
        
        Args:
            message: The user message to analyze
            
        Returns:
            dict: Context information including name, actions, and other metadata
        """
        if not message:
            return self.contexts.get('General', {
                'name': 'General',
                'description': 'Default conversational mode',
                'triggers': ['*'],
                'actions': ['maintain_conversation']
            })
            
        message_lower = message.lower()
        best_match = ('General', 0)
        
        # First check for exact matches in triggers
        for context_name, context in self.contexts.items():
            triggers = context.get('triggers', [])
            for trigger in triggers:
                if trigger == '*':
                    continue  # Skip wildcard for exact matching
                if trigger.lower() in message_lower:
                    # Direct match found, return immediately with high confidence
                    logger.info(f"Direct context match found: {context_name}")
                    return context
        
        # If no exact match, use fuzzy matching
        for context_name, context in self.contexts.items():
            triggers = context.get('triggers', [])
            for trigger in triggers:
                if trigger == '*':
                    continue  # Skip wildcard for fuzzy matching
                    
                similarity = fuzz.partial_ratio(message_lower, trigger.lower())
                if similarity > best_match[1] and similarity > 75:
                    best_match = (context_name, similarity)
        
        logger.info(f"Fuzzy context match found: {best_match[0]} with score {best_match[1]}")
        return self.contexts.get(best_match[0], self.contexts.get('General'))

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
- `compare [model1] [model2]` - Compare tractors

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
            return self._process_input(user_input)

        except Exception as e:
            logging.error(f"Error processing input: {e}")
            return self.handle_error(e)

    def _parse_context_data(self, text: str) -> List[Dict]:
        """Parse the structured text into context chunks"""
        sections = re.split(r'\n\d+\.\s+', text)
        return [{"text": section.strip()} for section in sections if section.strip()]

    def _process_input(self, user_input: str) -> str:
        """Process the user input and return a response (synchronous version)"""
        try:
            # Get relevant context from vector database
            context = []
            if self.vector_db and self.vector_db.is_available:
                # Generate a placeholder vector for the query
                query_vector = self.vector_db._generate_embedding(user_input)
                context = self.vector_db.query_context(query_vector=query_vector, top_k=3)
                logging.info(f"Found {len(context)} context items")
            else:
                # If VectorDB is not available, use a fallback context processor
                fallback_processor = FallbackContextProcessor()
                return fallback_processor.process_context(user_input)

            # Generate response using AI service
            if not self.ai_service or not self.ai_service.is_available:
                return "I apologize, but the AI service is not properly configured. Please check your GROQ_API_KEY."
                
            response = self.ai_service.generate_response(user_input, context)
            
            if not response:
                return "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
                
            return response

        except Exception as e:
            logging.error(f"Error processing input: {e}")
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"

    def process_context_file(self, filename="context_data.txt"):
        """Process context file (synchronous version)"""
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

    # Async versions for compatibility
    async def _process_input_async(self, user_input: str) -> str:
        """Async wrapper for _process_input"""
        return self._process_input(user_input)
    
    async def process_context_file_async(self, filename="context_data.txt"):
        """Async wrapper for process_context_file"""
        return self.process_context_file(filename)


class FallbackContextProcessor:
    """Fallback context processor for determining message context"""
    
    def __init__(self):
        """Initialize the context processor"""
        self.contexts = self._load_contexts()
        logger.info("Successfully initialized services")
    
    def _load_contexts(self) -> Dict[str, Dict[str, Any]]:
        """Load context definitions from file"""
        import json
        contexts = {}
        try:
            context_file = os.path.join(os.path.dirname(__file__), 'context_data.txt')
            if not os.path.exists(context_file):
                logger.warning(f"Context data file not found: {context_file}")
                # Add fallback general context
                contexts['General'] = {
                    'name': 'General',
                    'description': 'Provide helpful information about tractors and farming equipment.',
                    'triggers': ['help', 'information', 'general', 'question'],
                    'actions': ['Provide information', 'Answer questions'],
                    'response_format': 'Concise and informative'
                }
                return contexts
                
            with open(context_file, 'r') as f:
                context_data = json.load(f)
            
            # Process each context
            for context in context_data:
                contexts[context['name']] = context
                
            # Ensure we always have a General context
            if 'General' not in contexts:
                contexts['General'] = {
                    'name': 'General',
                    'description': 'Provide helpful information about tractors and farming equipment.',
                    'triggers': ['help', 'information', 'general', 'question'],
                    'actions': ['Provide information', 'Answer questions'],
                    'response_format': 'Concise and informative'
                }
                
            logger.info(f"Loaded {len(contexts)} contexts from {context_file}")
            return contexts
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing context data: {str(e)}")
            # Add fallback general context
            contexts['General'] = {
                'name': 'General',
                'description': 'Provide helpful information about tractors and farming equipment.',
                'triggers': ['help', 'information', 'general', 'question'],
                'actions': ['Provide information', 'Answer questions'],
                'response_format': 'Concise and informative'
            }
            return contexts
        except Exception as e:
            logger.error(f"Error loading contexts: {str(e)}")
            # Add fallback general context
            contexts['General'] = {
                'name': 'General',
                'description': 'Provide helpful information about tractors and farming equipment.',
                'triggers': ['help', 'information', 'general', 'question'],
                'actions': ['Provide information', 'Answer questions'],
                'response_format': 'Concise and informative'
            }
            return contexts
    
    def process_context(self, message: str) -> Dict[str, Any]:
        """Process message to determine context"""
        if not message:
            return self.contexts['General']
            
        message_lower = message.lower()
        best_match = ('General', 0)
        
        # Find best matching context based on triggers
        for context_name, context in self.contexts.items():
            for trigger in context['triggers']:
                similarity = fuzz.partial_ratio(message_lower, trigger.lower())
                if similarity > best_match[1] and similarity > 75:  # Threshold for matching
                    best_match = (context_name, similarity)
        
        logger.debug(f"Context determined: {best_match[0]} (score: {best_match[1]})")
        return self.contexts[best_match[0]]


def main():
    processor = ContextProcessor()
    console.clear()
    console.print(processor.welcome_note)
    processor.process_context_file()

if __name__ == "__main__":
    main()
