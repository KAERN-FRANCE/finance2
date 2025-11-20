"""
Main FastAPI application for the Meeting Assistant.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.config import settings
from backend.utils.logger import log
from backend.models.database import init_db
from backend.api import documents, meetings, reports, websocket
from backend.models.schemas import HealthResponse, ConfigResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    log.info("Starting Meeting Assistant API...")

    # Initialize database
    init_db()
    log.info("Database initialized")

    # Ensure directories exist
    settings.ensure_directories()
    log.info("Directories verified")

    # Initialize services (lazy loaded, but we can preload here if needed)
    log.info("Services ready")

    log.info(f"API running on {settings.host}:{settings.port}")

    yield

    # Shutdown
    log.info("Shutting down Meeting Assistant API...")


# Create FastAPI app
app = FastAPI(
    title="Meeting Assistant API",
    description="API for AI-powered meeting assistance with real-time transcription and analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router)
app.include_router(meetings.router)
app.include_router(reports.router)
app.include_router(websocket.router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Meeting Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check services
        services_status = {}

        # Check database
        try:
            from backend.models.database import SessionLocal
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            services_status["database"] = "ok"
        except Exception as e:
            services_status["database"] = f"error: {str(e)}"

        # Check vector store
        try:
            from backend.services.vector_store import get_vector_store
            vector_store = get_vector_store()
            vector_store.get_stats()
            services_status["vector_store"] = "ok"
        except Exception as e:
            services_status["vector_store"] = f"error: {str(e)}"

        # Check APIs
        services_status["openai_api"] = "configured" if settings.openai_api_key else "not configured"
        services_status["anthropic_api"] = "configured" if settings.anthropic_api_key else "not configured"

        # Overall status
        overall_status = "healthy" if all(
            status == "ok" or status == "configured"
            for status in services_status.values()
        ) else "degraded"

        return HealthResponse(
            status=overall_status,
            version="1.0.0",
            services=services_status
        )

    except Exception as e:
        log.error(f"Health check error: {e}")
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            services={"error": str(e)}
        )


@app.get("/api/config", response_model=ConfigResponse)
async def get_config():
    """Get application configuration (exposed to frontend)."""
    return ConfigResponse(
        supported_languages=settings.supported_languages_list,
        max_upload_size_mb=settings.max_upload_size_mb,
        max_meeting_duration_hours=settings.max_meeting_duration_hours,
        audio_chunk_duration_seconds=settings.audio_chunk_duration_seconds,
        supported_file_types=["pdf", "docx", "csv", "xlsx"]
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
