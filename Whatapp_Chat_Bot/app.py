"""WhatsApp Chat Bot Application - Flask Version"""
import json
import traceback
import os
from flask import Flask, render_template, request, jsonify, send_from_directory, session
from flask_cors import CORS
from services.ai_service import AIService
from services.vector_db import VectorDB
from config.settings import get_settings
from context_processor import ContextProcessor
from dotenv import load_dotenv

# Initialize logging
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set secret key for session management
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)
app.logger.setLevel(logging.INFO)

# Initialize services with fallback
ai_service = None
vector_db = None
try:
    # Initialize AI service (required)
    ai_service = AIService()
    if not ai_service.initialize():
        app.logger.error(f"Failed to initialize AI service: {ai_service.last_error}")
        raise Exception(f"AI service initialization failed: {ai_service.last_error}")
    app.logger.info("AI service initialized successfully")
    
    # Initialize Vector DB (optional)
    try:
        vector_db = VectorDB()
        vector_db.initialize()
        app.logger.info("Vector DB initialized successfully")
    except Exception as vdb_error:
        app.logger.warning(f"Vector DB initialization failed (optional): {str(vdb_error)}")
        app.logger.info("Continuing without Vector DB functionality")
except Exception as e:
    app.logger.error(f"Critical service initialization error: {str(e)}")
    app.logger.warning("Running in limited functionality mode")

@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    return "Server is running correctly"

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'Message field required'}), 400
    
    # Check if AI service is available
    if not ai_service or not ai_service.is_available:
        error_msg = "AI service is not available"
        app.logger.error(error_msg)
        return jsonify({'error': error_msg}), 503
    
    try:
        # Process message context
        context_info = ContextProcessor().process_context(data['message'])
        
        # Generate context-aware response
        response = ai_service.generate_response(
            message=data['message'],
            context_info=context_info
        )
        
        # Maintain context across session
        if 'context' not in session or context_info['name'] != 'General':
            session['context'] = context_info
        
        return jsonify({
            'response': response,
            'context': session['context']['name'],
            'suggested_actions': session['context']['actions']
        })
    except Exception as e:
        app.logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': f"Failed to process message: {str(e)}"}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/health')
def health_check():
    ai_status = ai_service is not None and ai_service.is_available
    vector_status = vector_db is not None and vector_db.is_available if vector_db else False
    
    status = "healthy" if ai_status else "critical"
    if ai_status and not vector_status:
        status = "degraded"
        
    return jsonify({
        "services": {
            "ai_service": ai_status,
            "vector_db": vector_status
        },
        "status": status,
        "message": "All required services operational" if status == "healthy" else 
                  "Core services operational, some features limited" if status == "degraded" else
                  "Critical services unavailable"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)