"""Job manager service for persistence and tracking."""
import json
import logging
import aiosqlite
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.models.job import Job, JobInput, JobStatus, JobResponse

logger = logging.getLogger(__name__)


class JobManager:
    """Manage job persistence and status tracking using SQLite."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.database_url.replace("sqlite:///", "")
        self._ensure_db_dir()
    
    def _ensure_db_dir(self):
        """Ensure the database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    async def init_db(self):
        """Initialize the database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    input_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    progress_percentage INTEGER DEFAULT 0,
                    status_message TEXT,
                    serp_data TEXT,
                    outline_data TEXT,
                    result TEXT,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT
                )
            """)
            await db.commit()
            logger.info("Database initialized successfully")
    
    async def create_job(self, job_input: JobInput) -> Job:
        """Create a new job and persist it.
        
        Args:
            job_input: Job input parameters
        
        Returns:
            Created Job instance
        """
        job = Job(input=job_input)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO jobs (
                    job_id, input_json, status, progress_percentage, status_message,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id,
                job.input.model_dump_json(),
                job.status.value,
                job.progress_percentage,
                job.status_message,
                job.created_at.isoformat(),
                job.updated_at.isoformat()
            ))
            await db.commit()
        
        logger.info(f"Created job: {job.job_id}")
        return job
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID.
        
        Args:
            job_id: Job identifier
        
        Returns:
            Job if found, None otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM jobs WHERE job_id = ?",
                (job_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_job(dict(row))
    
    async def update_job(self, job: Job):
        """Update job in database.
        
        Args:
            job: Job to update
        """
        job.updated_at = datetime.utcnow()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE jobs SET
                    status = ?,
                    progress_percentage = ?,
                    status_message = ?,
                    serp_data = ?,
                    outline_data = ?,
                    result = ?,
                    error_message = ?,
                    retry_count = ?,
                    updated_at = ?,
                    started_at = ?,
                    completed_at = ?
                WHERE job_id = ?
            """, (
                job.status.value,
                job.progress_percentage,
                job.status_message,
                json.dumps(job.serp_data) if job.serp_data else None,
                json.dumps(job.outline_data) if job.outline_data else None,
                json.dumps(job.result) if job.result else None,
                job.error_message,
                job.retry_count,
                job.updated_at.isoformat(),
                job.started_at.isoformat() if job.started_at else None,
                job.completed_at.isoformat() if job.completed_at else None,
                job.job_id
            ))
            await db.commit()
        
        logger.debug(f"Updated job {job.job_id}: status={job.status}")
    
    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Job]:
        """List jobs with optional filtering.
        
        Args:
            status: Optional status filter
            limit: Maximum number of jobs to return
            offset: Offset for pagination
        
        Returns:
            List of jobs
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if status:
                cursor = await db.execute(
                    "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (status.value, limit, offset)
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (limit, offset)
                )
            
            rows = await cursor.fetchall()
            return [self._row_to_job(dict(row)) for row in rows]
    
    async def get_resumable_jobs(self) -> List[Job]:
        """Get jobs that can be resumed after failure.
        
        Returns:
            List of resumable jobs
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM jobs 
                WHERE status = 'failed' 
                AND (serp_data IS NOT NULL OR outline_data IS NOT NULL)
                ORDER BY updated_at DESC
            """)
            rows = await cursor.fetchall()
            return [self._row_to_job(dict(row)) for row in rows]
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job.
        
        Args:
            job_id: Job identifier
        
        Returns:
            True if deleted, False if not found
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM jobs WHERE job_id = ?",
                (job_id,)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    def _row_to_job(self, row: dict) -> Job:
        """Convert database row to Job model.
        
        Args:
            row: Database row as dict
        
        Returns:
            Job instance
        """
        return Job(
            job_id=row["job_id"],
            input=JobInput.model_validate_json(row["input_json"]),
            status=JobStatus(row["status"]),
            progress_percentage=row["progress_percentage"],
            status_message=row["status_message"],
            serp_data=json.loads(row["serp_data"]) if row["serp_data"] else None,
            outline_data=json.loads(row["outline_data"]) if row["outline_data"] else None,
            result=json.loads(row["result"]) if row["result"] else None,
            error_message=row["error_message"],
            retry_count=row["retry_count"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
        )


# Singleton instance
job_manager = JobManager()
