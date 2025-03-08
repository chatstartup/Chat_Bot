# WhatsApp Chat Bot

An AI-powered WhatsApp Chat Bot with context-aware responses, built with FastAPI and modern best practices.

## Features

- **AI-Powered Responses**: Uses Groq for generating context-aware responses
- **Vector Database**: Pinecone integration for semantic search and context retrieval
- **Redis Caching**: Efficient caching and rate limiting
- **JWT Authentication**: Secure API endpoints
- **Prometheus Metrics**: Built-in monitoring
- **Docker Support**: Multi-stage builds and health checks
- **Comprehensive Testing**: Unit tests with pytest

## Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Redis
- Groq API Key
- Pinecone API Key

### Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Fill in the required environment variables in `.env`:
   - `GROQ_API_KEY`: Your Groq API key
   - `PINECONE_API_KEY`: Your Pinecone API key
   - `JWT_SECRET_KEY`: Secret key for JWT tokens
   - Redis configuration

### Running with Docker

1. Build and start the services:
   ```bash
   docker-compose up --build
   ```

2. Access the API documentation at http://localhost:8000/docs

### Running Locally

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   .\venv\Scripts\activate   # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   uvicorn app:app --reload
   ```

## API Endpoints

- `POST /chat`: Send a chat message
- `GET /chat/{session_id}`: Get chat session history
- `DELETE /chat/{session_id}`: Clear chat session
- `GET /health`: Service health check
- `GET /metrics`: Prometheus metrics

## Testing

Run the test suite:
```bash
pytest
```

## Monitoring

The application exposes Prometheus metrics at `/metrics`. Key metrics include:
- Request counts by endpoint and status
- Request latency by endpoint
- Service health status

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
