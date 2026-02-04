"""Main FastAPI application for SEO Article Generator."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import router
from app.services.job_manager import job_manager

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    # Startup
    logger.info("Starting SEO Article Generator API...")
    await job_manager.init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down SEO Article Generator API...")


# Create FastAPI app
app = FastAPI(
    title="SEO Article Generator",
    description="""
    An AI-powered backend service that generates SEO-optimized articles.
    
    ## Features
    - **SERP Analysis**: Analyzes top 10 search results for competitive insights
    - **Intelligent Outline**: Creates structured outlines based on successful content
    - **Full Article Generation**: Produces complete, publish-ready articles
    - **SEO Optimization**: Proper heading hierarchy, keyword placement, meta tags
    - **Quality Scoring**: Evaluates and validates content against SEO criteria
    - **Job Management**: Track, pause, and resume generation jobs
    
    ## Workflow
    1. Submit a topic via POST /generate
    2. Check job status via GET /jobs/{job_id}
    3. Resume failed jobs via POST /jobs/{job_id}/resume
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, tags=["articles"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "SEO Article Generator API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
