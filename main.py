import logging
import uvicorn
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from db_operations.presentation.routing import image_caption_router
from document_parser.presentation.routing import content_extractor
from rag_engine.presentation.routing import llm_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create all DB tables if they don't exist yet
    from db_operations.business_logic.db_tables import Base
    from db_operations.business_logic.db import engine
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic (if needed) goes here


# Initialize FastAPI app
app = FastAPI(title="RAGMU - RAG Studio", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(image_caption_router, prefix="/api")
app.include_router(content_extractor, prefix="/api")
app.include_router(llm_router, prefix="/api")

# Get static directory path
static_dir = Path(__file__).parent / "static"

# Mount static files (CSS, JS, images, etc.)
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Root endpoint with API info
@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "name": "RAGMU RAG Studio",
        "version": "1.0",
        "status": "running",
        "documentation": "/docs"
    }

# Health check endpoint
@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "RAGMU RAG Studio"}

# Serve index.html for the root path
@app.get("/")
async def serve_index():
    """Serve the RAG Studio web UI"""
    # 1) static/index.html  (Docker & production)
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path, media_type="text/html")
    # 2) root index.html fallback (local development)
    root_index = Path(__file__).parent / "index.html"
    if root_index.exists():
        return FileResponse(root_index, media_type="text/html")
    return {"message": "RAGMU RAG Studio - Web UI not found", "api_docs": "/docs"}

if __name__ == "__main__":
    # Get host and port from environment, with Docker-friendly defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run(app, host=host, port=port, log_level="info")

