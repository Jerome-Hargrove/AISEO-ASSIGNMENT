"""Main content generation agent that orchestrates the pipeline."""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.job import Job, JobStatus
from app.models.serp import SerpAnalysis
from app.models.article import ArticleOutline, GeneratedArticle
from app.services.serp_service import serp_service
from app.services.outline_generator import outline_generator
from app.services.article_generator import article_generator
from app.services.quality_scorer import quality_scorer
from app.services.job_manager import job_manager

logger = logging.getLogger(__name__)


class ContentAgent:
    """Main agent that orchestrates the content generation pipeline."""
    
    def __init__(self):
        self.max_retries = 2
        self.min_quality_score = 70.0
    
    async def process_job(self, job: Job) -> Job:
        """Process a content generation job through the full pipeline.
        
        Args:
            job: Job to process
        
        Returns:
            Updated job with results
        """
        try:
            # Determine starting point (for resume capability)
            start_stage = job.get_resume_stage() if job.can_resume() else JobStatus.SERP_ANALYSIS
            
            logger.info(f"Processing job {job.job_id} starting from {start_stage.value}")
            
            # Stage 1: SERP Analysis
            if start_stage == JobStatus.SERP_ANALYSIS:
                job = await self._stage_serp_analysis(job)
                if job.status == JobStatus.FAILED:
                    return job
            
            # Load SERP data from checkpoint
            serp_analysis = self._load_serp_analysis(job)
            if not serp_analysis:
                job.update_status(
                    JobStatus.FAILED,
                    "Failed to load SERP analysis data",
                    progress=0
                )
                await job_manager.update_job(job)
                return job
            
            # Stage 2: Outline Generation
            if start_stage in (JobStatus.SERP_ANALYSIS, JobStatus.OUTLINE_GENERATION):
                job = await self._stage_outline_generation(job, serp_analysis)
                if job.status == JobStatus.FAILED:
                    return job
            
            # Load outline from checkpoint
            article_outline = self._load_outline(job)
            if not article_outline:
                job.update_status(
                    JobStatus.FAILED,
                    "Failed to load outline data",
                    progress=30
                )
                await job_manager.update_job(job)
                return job
            
            # Stage 3: Content Generation
            job = await self._stage_content_generation(job, article_outline, serp_analysis)
            if job.status == JobStatus.FAILED:
                return job
            
            # Stage 4: Quality Check
            job = await self._stage_quality_check(job)
            
            return job
            
        except Exception as e:
            logger.error(f"Job {job.job_id} failed with error: {str(e)}")
            job.update_status(
                JobStatus.FAILED,
                f"Unexpected error: {str(e)}",
                progress=job.progress_percentage
            )
            job.error_message = str(e)
            await job_manager.update_job(job)
            return job
    
    async def _stage_serp_analysis(self, job: Job) -> Job:
        """Stage 1: Fetch and analyze SERP data.
        
        Args:
            job: Current job
        
        Returns:
            Updated job
        """
        try:
            job.update_status(
                JobStatus.SERP_ANALYSIS,
                "Analyzing search engine results...",
                progress=10
            )
            await job_manager.update_job(job)
            
            # Fetch and analyze SERP
            serp_analysis = await serp_service.get_full_analysis(job.input.topic)
            
            # Save checkpoint (mode='json' ensures datetime is serializable)
            job.serp_data = serp_analysis.model_dump(mode='json')
            job.update_status(
                JobStatus.OUTLINE_GENERATION,
                f"SERP analysis complete. Found {len(serp_analysis.topics)} topics.",
                progress=25
            )
            await job_manager.update_job(job)
            
            logger.info(f"Job {job.job_id}: SERP analysis complete")
            return job
            
        except Exception as e:
            logger.error(f"SERP analysis failed for job {job.job_id}: {str(e)}")
            job.update_status(
                JobStatus.FAILED,
                f"SERP analysis failed: {str(e)}",
                progress=10
            )
            job.error_message = str(e)
            await job_manager.update_job(job)
            return job
    
    async def _stage_outline_generation(
        self,
        job: Job,
        serp_analysis: SerpAnalysis
    ) -> Job:
        """Stage 2: Generate article outline.
        
        Args:
            job: Current job
            serp_analysis: SERP analysis data
        
        Returns:
            Updated job
        """
        try:
            job.update_status(
                JobStatus.OUTLINE_GENERATION,
                "Generating article outline...",
                progress=30
            )
            await job_manager.update_job(job)
            
            # Generate outline
            outline = await outline_generator.generate_outline(
                serp_analysis,
                job.input.target_word_count
            )
            
            # Save checkpoint (mode='json' ensures datetime is serializable)
            job.outline_data = outline.model_dump(mode='json')
            job.update_status(
                JobStatus.CONTENT_GENERATION,
                f"Outline ready: {len(outline.sections)} sections",
                progress=40
            )
            await job_manager.update_job(job)
            
            logger.info(f"Job {job.job_id}: Outline generation complete")
            return job
            
        except Exception as e:
            logger.error(f"Outline generation failed for job {job.job_id}: {str(e)}")
            job.update_status(
                JobStatus.FAILED,
                f"Outline generation failed: {str(e)}",
                progress=30
            )
            job.error_message = str(e)
            await job_manager.update_job(job)
            return job
    
    async def _stage_content_generation(
        self,
        job: Job,
        outline: ArticleOutline,
        serp_analysis: SerpAnalysis
    ) -> Job:
        """Stage 3: Generate full article content.
        
        Args:
            job: Current job
            outline: Article outline
            serp_analysis: SERP analysis data
        
        Returns:
            Updated job
        """
        try:
            job.update_status(
                JobStatus.CONTENT_GENERATION,
                "Writing article content...",
                progress=50
            )
            await job_manager.update_job(job)
            
            # Generate article
            article = await article_generator.generate_article(
                outline,
                serp_analysis,
                job.input.target_word_count
            )
            
            # Save result (mode='json' ensures datetime is serializable)
            job.result = article.model_dump(mode='json')
            job.update_status(
                JobStatus.QUALITY_CHECK,
                f"Article generated: {article.total_word_count} words",
                progress=80
            )
            await job_manager.update_job(job)
            
            logger.info(f"Job {job.job_id}: Content generation complete")
            return job
            
        except Exception as e:
            logger.error(f"Content generation failed for job {job.job_id}: {str(e)}")
            job.update_status(
                JobStatus.FAILED,
                f"Content generation failed: {str(e)}",
                progress=50
            )
            job.error_message = str(e)
            await job_manager.update_job(job)
            return job
    
    async def _stage_quality_check(self, job: Job) -> Job:
        """Stage 4: Evaluate quality and finalize.
        
        Args:
            job: Current job
        
        Returns:
            Updated job
        """
        try:
            job.update_status(
                JobStatus.QUALITY_CHECK,
                "Evaluating content quality...",
                progress=85
            )
            await job_manager.update_job(job)
            
            # Load article from result
            article = GeneratedArticle.model_validate(job.result)
            
            # Evaluate quality
            passes, score, issues = quality_scorer.passes_quality_check(
                article,
                job.input.target_word_count,
                self.min_quality_score
            )
            
            # Add quality info to result
            job.result["quality_score"] = score
            job.result["quality_issues"] = issues
            job.result["passes_quality_check"] = passes
            
            if passes:
                job.update_status(
                    JobStatus.COMPLETED,
                    f"Article complete! Quality score: {score:.1f}/100",
                    progress=100
                )
            else:
                # Still complete, but with quality warning
                job.update_status(
                    JobStatus.COMPLETED,
                    f"Article complete with quality concerns. Score: {score:.1f}/100",
                    progress=100
                )
            
            await job_manager.update_job(job)
            
            logger.info(f"Job {job.job_id}: Quality check complete, score={score:.1f}")
            return job
            
        except Exception as e:
            logger.error(f"Quality check failed for job {job.job_id}: {str(e)}")
            # Don't fail the job for quality check issues
            job.update_status(
                JobStatus.COMPLETED,
                "Article complete (quality check skipped)",
                progress=100
            )
            await job_manager.update_job(job)
            return job
    
    def _load_serp_analysis(self, job: Job) -> Optional[SerpAnalysis]:
        """Load SERP analysis from job checkpoint."""
        if not job.serp_data:
            return None
        try:
            return SerpAnalysis.model_validate(job.serp_data)
        except Exception as e:
            logger.error(f"Failed to load SERP analysis: {str(e)}")
            return None
    
    def _load_outline(self, job: Job) -> Optional[ArticleOutline]:
        """Load outline from job checkpoint."""
        if not job.outline_data:
            return None
        try:
            return ArticleOutline.model_validate(job.outline_data)
        except Exception as e:
            logger.error(f"Failed to load outline: {str(e)}")
            return None
    
    async def resume_job(self, job_id: str) -> Optional[Job]:
        """Resume a failed job from its last checkpoint.
        
        Args:
            job_id: Job to resume
        
        Returns:
            Updated job or None if not found
        """
        job = await job_manager.get_job(job_id)
        if not job:
            logger.warning(f"Job {job_id} not found for resume")
            return None
        
        if not job.can_resume():
            logger.warning(f"Job {job_id} cannot be resumed (no checkpoints)")
            return None
        
        job.retry_count += 1
        job.error_message = None
        
        return await self.process_job(job)


# Singleton instance
content_agent = ContentAgent()
