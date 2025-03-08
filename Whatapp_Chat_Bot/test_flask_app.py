import os
import logging
import asyncio
from flask import Flask, jsonify
from dotenv import load_dotenv, find_dotenv
from groq import AsyncGroq

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = find_dotenv()
if env_path:
    load_dotenv(env_path)
    logger.info(f"Loaded env from: {env_path}")

# Get API key
api_key = os.environ.get("GROQ_API_KEY")
logger.info(f"GROQ_API_KEY available: {bool(api_key)}")

app = Flask(__name__)

# Initialize Groq client
client = None
if api_key:
    try:
        client = AsyncGroq(api_key=api_key)
        logger.info("Successfully initialized Groq client")
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")

@app.route('/')
def index():
    return jsonify({"status": "ok", "client_initialized": client is not None})

@app.route('/test')
def test():
    if not client:
        return jsonify({"error": "Groq client not initialized"}), 500
    
    # Run async code with event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        response = loop.run_until_complete(generate_response("Hello, how are you?"))
        return jsonify({"response": response})
    finally:
        loop.close()

async def generate_response(prompt):
    try:
        completion = await client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="mixtral-8x7b-32768"
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True, port=5001)
