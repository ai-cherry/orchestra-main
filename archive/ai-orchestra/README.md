# AI Orchestra

AI Orchestra is a modern, AI-centric application framework designed for building intelligent applications with Google Cloud Platform services.

## Project Structure

The project follows a clean, modular architecture with clear separation of concerns:

```
ai-orchestra/
├── core/                  # Core framework components
│   ├── interfaces/        # Protocol definitions
│   ├── models/            # Domain models with Pydantic
│   ├── services/          # Business logic services
│   ├── config.py          # Configuration management
│   └── errors.py          # Error handling framework
├── infrastructure/        # Infrastructure components
│   ├── gcp/               # GCP-specific implementations
│   ├── security/          # Security implementations
│   └── persistence/       # Data storage implementations
├── api/                   # API endpoints and handlers
│   └── main.py            # FastAPI application
├── utils/                 # Utility functions and helpers
│   └── logging.py         # Structured logging utilities
└── run.py                 # Application entry point
```

## Key Features

- **Clean Architecture**: Clear separation of concerns with interfaces and implementations
- **Type Safety**: Comprehensive type hints throughout the codebase
- **Structured Logging**: Machine-parseable logging format for better observability
- **Error Handling**: Consistent error handling with detailed error information
- **Configuration Management**: Type-safe configuration with validation
- **Dependency Injection**: Simple dependency injection without complex frameworks
- **AI Integration**: Seamless integration with Google Vertex AI

## Core Interfaces

### Memory Provider

The `MemoryProvider` interface defines a protocol for storing and retrieving data:

```python
class MemoryProvider(Protocol):
    async def store(self, key: str, value: Any, ttl: Optional[int] = None) -> bool: ...
    async def retrieve(self, key: str) -> Optional[Any]: ...
    async def delete(self, key: str) -> bool: ...
    async def exists(self, key: str) -> bool: ...
    async def list_keys(self, pattern: str = "*") -> List[str]: ...
```

### AI Service

The `AIService` interface defines a protocol for AI model interactions:

```python
class AIService(Protocol):
    async def generate_text(self, prompt: str, model_id: str, ...) -> str: ...
    async def generate_embeddings(self, texts: List[str], model_id: str) -> List[List[float]]: ...
    async def classify_text(self, text: str, categories: List[str], model_id: str) -> Dict[str, float]: ...
    async def answer_question(self, question: str, context: str, model_id: str) -> str: ...
    async def summarize_text(self, text: str, max_length: Optional[int] = None, model_id: str = "default") -> str: ...
    async def get_available_models(self) -> List[Dict[str, Any]]: ...
```

## Implementations

### Firestore Memory Provider

The `FirestoreMemoryProvider` implements the `MemoryProvider` interface using Google Cloud Firestore:

```python
memory_provider = FirestoreMemoryProvider()
await memory_provider.store("key", "value", ttl=3600)
value = await memory_provider.retrieve("key")
```

### Vertex AI Service

The `VertexAIService` implements the `AIService` interface using Google Cloud Vertex AI:

```python
ai_service = VertexAIService()
text = await ai_service.generate_text("Hello, world!", model_id="gemini-pro")
embeddings = await ai_service.generate_embeddings(["Hello, world!"], model_id="text-embedding")
```

## API Endpoints

The FastAPI application provides the following endpoints:

- `GET /`: Root endpoint with API information
- `GET /health`: Health check endpoint
- `POST /generate-text`: Generate text from a prompt
- `POST /generate-embeddings`: Generate embeddings for a list of texts
- `POST /classify-text`: Classify text into categories
- `POST /answer-question`: Answer a question based on context
- `POST /summarize-text`: Summarize text
- `GET /models`: Get available models
- `POST /memory/store`: Store a value in memory
- `POST /memory/retrieve`: Retrieve a value from memory
- `DELETE /memory/{key}`: Delete a value from memory
- `GET /memory/keys`: List memory keys matching a pattern

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Google Cloud Platform account
- Google Cloud SDK

### Installation

1. Clone the repository:

```bash
git clone https://github.com/your-organization/ai-orchestra.git
cd ai-orchestra
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
export GCP_PROJECT_ID=your-project-id
export GCP_REGION=us-west4
```

### Running the Application

Run the application with:

```bash
python -m ai_orchestra.run
```

Or with custom settings:

```bash
python -m ai_orchestra.run --host 0.0.0.0 --port 8080 --reload
```

## Development

### Adding a New Interface

1. Create a new file in `core/interfaces/`
2. Define a Protocol class with required methods
3. Add type hints and docstrings

### Adding a New Implementation

1. Create a new file in the appropriate directory
2. Implement the interface
3. Add to dependency injection in `api/main.py`

## Deployment

### Google Cloud Run

Deploy to Google Cloud Run with:

```bash
gcloud run deploy ai-orchestra \
  --source . \
  --region us-west4 \
  --platform managed \
  --allow-unauthenticated
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
