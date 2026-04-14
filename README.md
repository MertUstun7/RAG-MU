# RAGMU - Retrieval-Augmented Generation Multi-modal Utility

A comprehensive RAG (Retrieval-Augmented Generation) system that combines document processing, vector search, and multi-modal AI capabilities for intelligent information retrieval and generation.

## Features

- **Web UI** - RAG Studio interface for interactive document analysis and querying
- **Document Processing** - Extract and parse documents with semantic chunking
- **Vector Search** - Hybrid search combining semantic similarity and BM25 keyword search
- **Image Captioning** - Qwen 2.5-VL model for automatic image descriptions
- **Local LLM Integration** - Ollama for running language models locally
- **Multi-modal Retrieval** - Retrieve both text and images based on queries
- **Persistent Storage** - SQLAlchemy ORM with PostgreSQL and Chroma vector DB
- **REST API** - FastAPI with full CORS support

## Technology Stack

### Core Framework
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

### AI/ML Components
- **LangChain** - LLM chains and orchestration
- **Ollama** - Local LLM inference
- **Hugging Face** - Embeddings and models
- **Qwen 2.5-VL** - Vision-Language model
- **Sentence Transformers** - Embedding generation
- **PyTorch** - Deep learning framework

### Database & Storage
- **PostgreSQL** - Relational database
- **SQLAlchemy** - ORM
- **Chroma** - Vector database

### Search & Retrieval
- **BM25** - Hybrid keyword search
- **FAISS** - Vector similarity search
- **CrossEncoder** - Result re-ranking

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (recommended)
- NVIDIA GPU (optional, for faster inference)

### Using Docker (Recommended)

#### Windows
```batch
# Full setup
setup.bat init

# Or manual steps
copy .env.example .env
docker-compose build
docker-compose up -d
```

#### Linux/Mac
```bash
# Full setup
./setup.sh init

# Or manual steps
cp .env.example .env
docker-compose build
docker-compose up -d
```

**Access the application:**
- **Web UI**: http://localhost:8000 (RAG Studio)
- **API Documentation**: http://localhost:8000/docs
- **Database UI**: http://localhost:5050 (pgAdmin)

### Local Development Setup

1. **Clone the repository**
   ```bash
   cd RAGMU
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Setup database**
   ```bash
   # Create tables
   python -c "from db_operations.business_logic.db import Base, engine; Base.metadata.create_all(engine)"
   ```

6. **Start Ollama** (in separate terminal)
   ```bash
   ollama serve
   ```

7. **Run the application**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

## Project Structure

```
RAGMU/
├── db_operations/          # Database operations and models
│   ├── business_logic/     # DB utilities and image storage
│   └── presentation/       # Database routes
├── document_parser/        # Document processing
│   ├── business_logic/     # Document extraction
│   └── presentation/       # Document routes
├── image_captioning/       # Image analysis
│   ├── business_logic/     # Qwen image captioning
│   └── presentation/       # Image caption routes
├── rag_engine/            # RAG core logic
│   ├── business_logic/     # Semantic search and answer generation
│   └── presentation/       # RAG API routes
├── vector_database/       # Vector DB operations
│   ├── business_logic/     # Chroma integration
│   └── presentation/       # Vector DB routes
├── main.py                # FastAPI application entry point
├── config.py              # Logging configuration
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Multi-service orchestration
├── Dockerfile             # Application container
└── README.md              # This file
```

## API Endpoints

### Web UI & Documentation
```bash
GET /
# Returns: index.html (RAG Studio Web Interface)

GET /docs
# Swagger UI interactive API documentation

GET /redoc
# ReDoc alternative API documentation

GET /api/info
# API information endpoint

GET /api/health
# Health check endpoint
```

### Document Processing
```bash
POST /api/documents/upload
# Upload and parse documents

GET /api/documents
# List uploaded documents
```

### Image Captioning
```bash
POST /api/images/caption
# Generate captions for images

GET /api/images
# List images
```

### RAG Query
```bash
POST /api/rag/query
# Submit a query and get RAG-enhanced response

GET /api/rag/search
# Search documents
```

### Models
```bash
GET /api/models
# List available Ollama models
```

## Configuration

### Environment Variables (.env)

```bash
# Database
DB_USER=ragmu_user
DB_PASSWORD=ragmu_password
DB_NAME=ragmu_db
DB_PORT=5432

# Application
APP_PORT=8000
LOG_LEVEL=INFO

# Ollama
OLLAMA_PORT=11434
OLLAMA_BASE_URL=http://ollama:11434

# pgAdmin
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin
PGADMIN_PORT=5050
```

## Docker Deployment

### Using Setup Scripts

```bash
# Windows
setup.bat init          # Full initialization
setup.bat start         # Start services
setup.bat logs          # View logs
setup.bat status        # Check status
setup.bat stop          # Stop services

# Linux/Mac
./setup.sh init         # Full initialization
./setup.sh start        # Start services
./setup.sh logs         # View logs
./setup.sh status       # Check status
./setup.sh stop         # Stop services
```

### Manual Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Full cleanup (removes volumes)
docker-compose down -v
```

## Services

| Service | Port | Purpose |
|---------|------|---------|
| FastAPI App | 8000 | Main application |
| PostgreSQL | 5432 | Database |
| Ollama | 11434 | Local LLM |
| pgAdmin | 5050 | Database management |

## GPU Support

To enable GPU acceleration for faster inference:

1. Install [NVIDIA Docker Runtime](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

2. Uncomment GPU sections in `docker-compose.yml`:
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: 1
             capabilities: [gpu]
   ```

3. Verify GPU access:
   ```bash
   docker-compose exec app python -c "import torch; print(torch.cuda.is_available())"
   ```

## Development

### Hot Reload

Use the development compose override:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

This enables:
- Code hot reload
- Debug logging
- Direct volume mounting
- Debug port exposure

### Database Management

Access pgAdmin at `http://localhost:5050` to:
- View tables
- Run SQL queries
- Manage database structure

### Ollama Model Management

Pull and manage models:
```bash
# List models
docker-compose exec ollama ollama list

# Pull a model
docker-compose exec ollama ollama pull mistral

# Run a model
docker-compose exec ollama ollama run mistral
```

## Documentation

- **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)** - Comprehensive Docker deployment guide
- **[DOCKER_QUICK_REFERENCE.md](DOCKER_QUICK_REFERENCE.md)** - Common Docker commands
- **[ANALYSIS_AND_DOCKER_SETUP.md](ANALYSIS_AND_DOCKER_SETUP.md)** - Project analysis and architecture

## Performance Optimization

1. **Vector Database** - Chroma with SQLite supports up to 1M documents
2. **Batch Processing** - Vector DB uses batch_size=500
3. **GPU Acceleration** - Enable for real-time inference
4. **Model Caching** - Ollama caches models in volumes
5. **Search Strategy** - Hybrid search combines semantic + keyword matching

## Production Deployment

For production:

1. Change default passwords in `.env`
2. Use PostgreSQL with replication
3. Implement authentication middleware
4. Set up monitoring and logging
5. Use reverse proxy (Nginx)
6. Enable HTTPS/SSL
7. Configure resource limits
8. Set up backup and recovery

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md#production-considerations) for detailed guidance.

## Troubleshooting

### Port Already in Use
Change ports in `.env` before starting services:
```bash
APP_PORT=8001
DB_PORT=5433
OLLAMA_PORT=11435
```

### Services Won't Start
Check logs:
```bash
docker-compose logs <service_name>
```

### Database Connection Issues
```bash
docker-compose exec postgres pg_isready -U ragmu_user
```

### Out of Memory
Increase Docker memory allocation or reduce model size.

See [DOCKER_QUICK_REFERENCE.md](DOCKER_QUICK_REFERENCE.md) for more troubleshooting.

## Contributing

1. Create a feature branch
2. Make your changes
3. Test locally with docker-compose
4. Submit a pull request

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [Ollama](https://ollama.ai/)
- [Chroma](https://www.trychroma.com/)
- [PostgreSQL](https://www.postgresql.org/)
