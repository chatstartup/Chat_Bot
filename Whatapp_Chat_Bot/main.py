from flask import Flask, request, jsonify, render_template
import socket
import logging
from utils import LanguageProcessor, VectorDB
from services.ai_service import AIService
from context_processor import ContextProcessor

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize services
try:
    language_processor = LanguageProcessor()
    logger.info("Successfully initialized LanguageProcessor")
except Exception as e:
    logger.error(f"Error initializing LanguageProcessor: {str(e)}")
    language_processor = None

try:
    vector_db = VectorDB()
    logger.info("Successfully initialized VectorDB")
except Exception as e:
    logger.error(f"Error initializing VectorDB: {str(e)}")
    vector_db = None

try:
    # Initialize context processor with vector_db
    context_processor = ContextProcessor(vector_db=vector_db)
    logger.info("Successfully initialized ContextProcessor")
except Exception as e:
    logger.error(f"Error initializing ContextProcessor: {str(e)}")
    context_processor = None

try:
    # Initialize AI service with vector_db and context_processor
    ai_service = AIService(vector_db=vector_db, context_processor=context_processor)
    logger.info("Successfully initialized AIService")
    
    # Update context_processor with ai_service to complete the dependency chain
    if context_processor:
        context_processor.ai_service = ai_service
except Exception as e:
    logger.error(f"Error initializing AIService: {str(e)}")
    ai_service = None

if not ai_service:
    logger.error("Failed to initialize AIService, application may not function correctly")

@app.route('/')
def index():
    """Serve the chat interface"""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    try:
        # Get request data
        request_data = request.json
        message = request_data.get('message')
        session_id = request_data.get('session_id')
        
        # Process message
        logger.info(f"Received chat request with session_id: {session_id}")
        
        # Check if AI service is available
        if not ai_service:
            logger.error("AI service is not available")
            return jsonify({"response": "I'm sorry, the AI service is currently unavailable. Please try again later."})
        
        # Generate response
        response = ai_service.generate_response(message=message)
        
        return jsonify({"response": response})
    
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        return jsonify({"response": f"Error: {str(e)}"})

@app.route('/health')
def health_check():
    return jsonify({
        "status": "operational",
        "services": {
            "ai_service": ai_service.health_check() if ai_service else "unavailable",
            "vector_db": "available" if vector_db and vector_db.index else "unavailable",
            "context_processor": "available" if context_processor else "unavailable"
        }
    })

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

if __name__ == "__main__":
    logger.info("Starting WhatsApp Chat Bot web application")
    port = 8080
    max_attempts = 5
    
    for attempt in range(max_attempts):
        if not is_port_in_use(port):
            logger.info(f'Starting server on port {port}')
            app.run(host='0.0.0.0', port=port, debug=True)
            break
        else:
            logger.warning(f'Port {port} is already in use, trying next port')
            port += 1
    else:
        logger.error('Failed to find available port after 5 attempts')
