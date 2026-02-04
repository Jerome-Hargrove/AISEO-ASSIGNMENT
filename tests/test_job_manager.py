"""Tests for job manager service."""
import pytest
import os
import tempfile
from datetime import datetime

from app.models.job import Job, JobInput, JobStatus
from app.services.job_manager import JobManager


@pytest.fixture
async def job_manager():
    """Create a JobManager with a temporary database."""
    # Use a temporary file for testing
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    manager = JobManager(db_path=db_path)
    await manager.init_db()
    
    yield manager
    
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def sample_job_input():
    """Create sample job input."""
    return JobInput(
        topic="best productivity tools for remote teams",
        target_word_count=1500,
        language="en"
    )


class TestJobManager:
    """Test suite for job manager."""
    
    @pytest.mark.asyncio
    async def test_create_job(self, job_manager, sample_job_input):
        """Test job creation."""
        job = await job_manager.create_job(sample_job_input)
        
        assert job.job_id is not None
        assert job.status == JobStatus.PENDING
        assert job.input.topic == sample_job_input.topic
        assert job.progress_percentage == 0
    
    @pytest.mark.asyncio
    async def test_get_job(self, job_manager, sample_job_input):
        """Test retrieving a job."""
        created_job = await job_manager.create_job(sample_job_input)
        
        retrieved_job = await job_manager.get_job(created_job.job_id)
        
        assert retrieved_job is not None
        assert retrieved_job.job_id == created_job.job_id
        assert retrieved_job.input.topic == sample_job_input.topic
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_job(self, job_manager):
        """Test retrieving a non-existent job returns None."""
        job = await job_manager.get_job("nonexistent-id")
        assert job is None
    
    @pytest.mark.asyncio
    async def test_update_job(self, job_manager, sample_job_input):
        """Test updating a job."""
        job = await job_manager.create_job(sample_job_input)
        
        # Update status
        job.update_status(JobStatus.SERP_ANALYSIS, "Analyzing...", 25)
        job.serp_data = {"keyword": "test", "results": []}
        await job_manager.update_job(job)
        
        # Retrieve and verify
        updated_job = await job_manager.get_job(job.job_id)
        
        assert updated_job.status == JobStatus.SERP_ANALYSIS
        assert updated_job.progress_percentage == 25
        assert updated_job.serp_data is not None
    
    @pytest.mark.asyncio
    async def test_list_jobs(self, job_manager, sample_job_input):
        """Test listing jobs."""
        # Create multiple jobs
        for _ in range(5):
            await job_manager.create_job(sample_job_input)
        
        jobs = await job_manager.list_jobs()
        
        assert len(jobs) == 5
    
    @pytest.mark.asyncio
    async def test_list_jobs_with_status_filter(self, job_manager, sample_job_input):
        """Test listing jobs with status filter."""
        # Create jobs with different statuses
        job1 = await job_manager.create_job(sample_job_input)
        job2 = await job_manager.create_job(sample_job_input)
        
        # Update one to completed
        job1.update_status(JobStatus.COMPLETED, "Done", 100)
        await job_manager.update_job(job1)
        
        # Filter by pending
        pending_jobs = await job_manager.list_jobs(status=JobStatus.PENDING)
        completed_jobs = await job_manager.list_jobs(status=JobStatus.COMPLETED)
        
        assert len(pending_jobs) == 1
        assert len(completed_jobs) == 1
    
    @pytest.mark.asyncio
    async def test_delete_job(self, job_manager, sample_job_input):
        """Test deleting a job."""
        job = await job_manager.create_job(sample_job_input)
        
        deleted = await job_manager.delete_job(job.job_id)
        assert deleted is True
        
        # Verify it's gone
        retrieved = await job_manager.get_job(job.job_id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_job(self, job_manager):
        """Test deleting non-existent job returns False."""
        deleted = await job_manager.delete_job("nonexistent-id")
        assert deleted is False


class TestJobModel:
    """Test Job model functionality."""
    
    def test_job_creation(self, sample_job_input):
        """Test job model creation."""
        job = Job(input=sample_job_input)
        
        assert job.job_id is not None
        assert job.status == JobStatus.PENDING
        assert job.progress_percentage == 0
    
    def test_update_status(self, sample_job_input):
        """Test status update method."""
        job = Job(input=sample_job_input)
        
        job.update_status(JobStatus.SERP_ANALYSIS, "Analyzing search results", 25)
        
        assert job.status == JobStatus.SERP_ANALYSIS
        assert job.status_message == "Analyzing search results"
        assert job.progress_percentage == 25
        assert job.started_at is not None
    
    def test_can_resume_with_serp_data(self, sample_job_input):
        """Test resume capability with SERP checkpoint."""
        job = Job(input=sample_job_input)
        job.status = JobStatus.FAILED
        job.serp_data = {"keyword": "test"}
        
        assert job.can_resume() is True
        assert job.get_resume_stage() == JobStatus.OUTLINE_GENERATION
    
    def test_can_resume_with_outline_data(self, sample_job_input):
        """Test resume capability with outline checkpoint."""
        job = Job(input=sample_job_input)
        job.status = JobStatus.FAILED
        job.serp_data = {"keyword": "test"}
        job.outline_data = {"title": "Test"}
        
        assert job.can_resume() is True
        assert job.get_resume_stage() == JobStatus.CONTENT_GENERATION
    
    def test_cannot_resume_without_checkpoints(self, sample_job_input):
        """Test job cannot resume without checkpoints."""
        job = Job(input=sample_job_input)
        job.status = JobStatus.FAILED
        
        assert job.can_resume() is False


class TestJobInput:
    """Test JobInput model."""
    
    def test_default_values(self):
        """Test default values are set correctly."""
        job_input = JobInput(topic="test topic")
        
        assert job_input.target_word_count == 1500
        assert job_input.language == "en"
    
    def test_custom_values(self):
        """Test custom values are accepted."""
        job_input = JobInput(
            topic="test topic",
            target_word_count=2000,
            language="es"
        )
        
        assert job_input.target_word_count == 2000
        assert job_input.language == "es"
    
    def test_word_count_validation(self):
        """Test word count must be within range."""
        with pytest.raises(ValueError):
            JobInput(topic="test", target_word_count=100)  # Below minimum
        
        with pytest.raises(ValueError):
            JobInput(topic="test", target_word_count=20000)  # Above maximum
