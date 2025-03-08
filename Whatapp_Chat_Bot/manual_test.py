"""Manual test script for WhatsApp Chat Bot"""
import requests
import json
import time
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
HOST = "http://localhost:8000"
SESSION_ID = f"manual-test-{int(time.time())}"

def print_separator():
    """Print a separator line"""
    print("\n" + "="*50 + "\n")

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    
    try:
        response = requests.get(f"{HOST}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200 and response.json().get("status") == "healthy":
            print("✅ Health check passed!")
        else:
            print("❌ Health check failed!")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print_separator()

def test_chat(message):
    """Test chat endpoint with a message"""
    print(f"Testing chat endpoint with message: '{message}'")
    
    try:
        payload = {
            "message": message,
            "session_id": SESSION_ID
        }
        
        print(f"Request: {json.dumps(payload, indent=2)}")
        
        start_time = time.time()
        response = requests.post(f"{HOST}/chat", json=payload)
        elapsed_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {elapsed_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            print(f"AI Response: {data.get('response')}")
            print(f"Session ID: {data.get('session_id')}")
            print("✅ Chat request successful!")
        else:
            print(f"❌ Chat request failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print_separator()

def interactive_mode():
    """Interactive chat mode"""
    print("\n🤖 WhatsApp Chat Bot Interactive Mode 🤖")
    print("Type 'exit' to quit\n")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        
        try:
            payload = {
                "message": user_input,
                "session_id": SESSION_ID
            }
            
            response = requests.post(f"{HOST}/chat", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                print(f"Bot: {data.get('response')}")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

def main():
    """Main function"""
    print("\n🤖 WhatsApp Chat Bot Manual Test 🤖")
    print(f"Server: {HOST}")
    print(f"Session ID: {SESSION_ID}")
    print_separator()
    
    # Test health endpoint
    test_health()
    
    # Test chat with predefined messages
    test_messages = [
        "Hello, how are you?",
        "Tell me about yourself",
        "What can you help me with?",
        "Thank you for your help"
    ]
    
    for message in test_messages:
        test_chat(message)
    
    # Interactive mode
    interactive_mode()

if __name__ == "__main__":
    # Check if server is running
    try:
        requests.get(f"{HOST}/health", timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Cannot connect to server at {HOST}")
        print("Please make sure the server is running with: python app.py")
        sys.exit(1)
    
    main()
