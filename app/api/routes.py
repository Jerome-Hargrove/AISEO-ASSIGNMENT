"""API routes for the SEO article generator."""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.models.job import JobInput, Job, JobStatus, JobResponse
from app.services.job_manager import job_manager
from app.services.agent import content_agent

logger = logging.getLogger(__name__)

router = APIRouter()


class GenerateRequest(BaseModel):
    """Request body for article generation."""
    topic: str
    target_word_count: int = 1500
    language: str = "en"


class GenerateResponse(BaseModel):
    """Response for job creation."""
    job_id: str
    status: str
    message: str


@router.post("/generate", response_model=GenerateResponse)
async def generate_article(
    request: GenerateRequest,
    background_tasks: BackgroundTasks
):
    """Submit a new article generation job.
    
    The job will be processed asynchronously. Use the /jobs/{job_id} endpoint
    to check status and retrieve results.
    """
    try:
        # Create job input
        job_input = JobInput(
            topic=request.topic,
            target_word_count=request.target_word_count,
            language=request.language
        )
        
        # Create job in database
        job = await job_manager.create_job(job_input)
        
        # Process job in background
        background_tasks.add_task(process_job_async, job.job_id)
        
        return GenerateResponse(
            job_id=job.job_id,
            status=job.status.value,
            message=f"Job created successfully. Topic: '{request.topic}'"
        )
        
    except Exception as e:
        logger.error(f"Failed to create job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_job_async(job_id: str):
    """Background task to process a job."""
    try:
        job = await job_manager.get_job(job_id)
        if job:
            await content_agent.process_job(job)
    except Exception as e:
        logger.error(f"Background job processing failed for {job_id}: {str(e)}")


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """Get the status and result of a job."""
    job = await job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return JobResponse.from_job(job)


@router.post("/jobs/{job_id}/resume", response_model=GenerateResponse)
async def resume_job(job_id: str, background_tasks: BackgroundTasks):
    """Resume a failed job from its last checkpoint."""
    job = await job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    if not job.can_resume():
        raise HTTPException(
            status_code=400,
            detail="Job cannot be resumed (no checkpoints available)"
        )
    
    # Reset status and retry
    job.status = job.get_resume_stage()
    job.error_message = None
    await job_manager.update_job(job)
    
    # Process in background
    background_tasks.add_task(process_job_async, job_id)
    
    return GenerateResponse(
        job_id=job.job_id,
        status=job.status.value,
        message=f"Job resumed from {job.status.value}"
    )


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List all jobs with optional status filter."""
    status_filter = None
    if status:
        try:
            status_filter = JobStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Valid values: {[s.value for s in JobStatus]}"
            )
    
    jobs = await job_manager.list_jobs(
        status=status_filter,
        limit=limit,
        offset=offset
    )
    
    return [JobResponse.from_job(job) for job in jobs]


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job."""
    deleted = await job_manager.delete_job(job_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return {"message": f"Job {job_id} deleted successfully"}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "seo-article-generator"
    }
