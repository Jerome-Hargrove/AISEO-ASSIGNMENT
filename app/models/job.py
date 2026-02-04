"""Job management data models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


class JobStatus(str, Enum):
    """Job processing status."""
    PENDING = "pending"
    SERP_ANALYSIS = "serp_analysis"
    OUTLINE_GENERATION = "outline_generation"
    CONTENT_GENERATION = "content_generation"
    QUALITY_CHECK = "quality_check"
    COMPLETED = "completed"
    FAILED = "failed"


class JobInput(BaseModel):
    """Input parameters for article generation job."""
    
    topic: str = Field(..., min_length=3, max_length=200, description="Topic or primary keyword")
    target_word_count: int = Field(default=1500, ge=500, le=10000, description="Target word count")
    language: str = Field(default="en", description="Language code (e.g., 'en', 'es')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "best productivity tools for remote teams",
                "target_word_count": 1500,
                "language": "en"
            }
        }


class Job(BaseModel):
    """Article generation job with full state tracking."""
    
    # Identification
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique job identifier")
    
    # Input
    input: JobInput = Field(..., description="Job input parameters")
    
    # Status tracking
    status: JobStatus = Field(default=JobStatus.PENDING, description="Current job status")
    progress_percentage: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    status_message: Optional[str] = Field(None, description="Human-readable status message")
    
    # Intermediate results (for resume capability)
    serp_data: Optional[Dict[str, Any]] = Field(None, description="Serialized SERP analysis data")
    outline_data: Optional[Dict[str, Any]] = Field(None, description="Serialized outline data")
    
    # Final result
    result: Optional[Dict[str, Any]] = Field(None, description="Serialized generated article")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Job creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    started_at: Optional[datetime] = Field(None, description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    
    def update_status(self, status: JobStatus, message: Optional[str] = None, progress: Optional[int] = None) -> None:
        """Update job status with timestamp."""
        self.status = status
        self.updated_at = datetime.utcnow()
        
        if message:
            self.status_message = message
        
        if progress is not None:
            self.progress_percentage = progress
        
        if status == JobStatus.SERP_ANALYSIS and not self.started_at:
            self.started_at = datetime.utcnow()
        
        if status in (JobStatus.COMPLETED, JobStatus.FAILED):
            self.completed_at = datetime.utcnow()
    
    def can_resume(self) -> bool:
        """Check if job can be resumed from a checkpoint."""
        return (
            self.status in (JobStatus.FAILED, JobStatus.SERP_ANALYSIS, JobStatus.OUTLINE_GENERATION)
            and (self.serp_data is not None or self.outline_data is not None)
        )
    
    def get_resume_stage(self) -> JobStatus:
        """Get the stage to resume from."""
        if self.outline_data:
            return JobStatus.CONTENT_GENERATION
        elif self.serp_data:
            return JobStatus.OUTLINE_GENERATION
        return JobStatus.SERP_ANALYSIS


class JobResponse(BaseModel):
    """API response for job status."""
    
    job_id: str
    status: JobStatus
    progress_percentage: int
    status_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    @classmethod
    def from_job(cls, job: Job) -> "JobResponse":
        """Create response from job model."""
        return cls(
            job_id=job.job_id,
            status=job.status,
            progress_percentage=job.progress_percentage,
            status_message=job.status_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
            result=job.result,
            error_message=job.error_message
        )
