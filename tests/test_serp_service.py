"""Tests for SERP service."""
import pytest
from unittest.mock import AsyncMock, patch

from app.models.serp import SerpResult, SerpAnalysis
from app.services.serp_service import SerpService


@pytest.fixture
def serp_service():
    """Create a SerpService instance."""
    return SerpService()


class TestSerpService:
    """Test suite for SERP service."""
    
    def test_mock_results_productivity(self, serp_service):
        """Test mock results for productivity-related queries."""
        results = serp_service._get_mock_results("best productivity tools for remote teams")
        
        assert len(results) == 10
        assert all(isinstance(r, SerpResult) for r in results)
        assert results[0].rank == 1
        assert results[9].rank == 10
        assert "productivity" in results[0].title.lower() or "productivity" in results[0].snippet.lower()
    
    def test_mock_results_seo(self, serp_service):
        """Test mock results for SEO-related queries."""
        results = serp_service._get_mock_results("seo best practices")
        
        assert len(results) == 10
        assert all(r.url.startswith("https://") for r in results)
        assert any("seo" in r.title.lower() for r in results)
    
    def test_mock_results_generic(self, serp_service):
        """Test mock results for generic queries."""
        results = serp_service._get_mock_results("machine learning basics")
        
        assert len(results) == 10
        # Generic results should have the keyword in title
        assert all("machine learning" in r.title.lower() for r in results)
    
    def test_serp_result_model(self):
        """Test SerpResult model validation."""
        result = SerpResult(
            rank=1,
            url="https://example.com/article",
            title="Test Article",
            snippet="This is a test snippet",
            domain="example.com"
        )
        
        assert result.rank == 1
        assert result.url == "https://example.com/article"
        assert result.domain == "example.com"
    
    def test_serp_result_rank_validation(self):
        """Test rank must be within valid range."""
        with pytest.raises(ValueError):
            SerpResult(
                rank=0,  # Invalid - must be >= 1
                url="https://example.com",
                title="Test",
                snippet="Test"
            )
    
    @pytest.mark.asyncio
    async def test_fetch_serp_results_no_api_key(self, serp_service):
        """Test fallback to mock data when API key is not configured."""
        serp_service.api_key = ""
        
        results = await serp_service.fetch_serp_results("test query")
        
        assert len(results) == 10
        assert all(isinstance(r, SerpResult) for r in results)
    
    @pytest.mark.asyncio
    async def test_analyze_results_structure(self, serp_service):
        """Test that analysis returns proper structure."""
        mock_results = serp_service._get_mock_results("productivity tools")
        
        # Mock the LLM client
        with patch('app.services.serp_service.llm_client') as mock_llm:
            mock_llm.generate_json = AsyncMock(return_value={
                "common_themes": ["productivity", "collaboration"],
                "topics": [{"topic": "Project Management", "frequency": 5, "importance": "high"}],
                "primary_keywords": ["productivity tools"],
                "secondary_keywords": ["team software"],
                "questions": [{"question": "What are the best tools?", "source": "serp"}]
            })
            
            analysis = await serp_service.analyze_results("productivity tools", mock_results)
        
        assert isinstance(analysis, SerpAnalysis)
        assert analysis.keyword == "productivity tools"
        assert analysis.total_results == 10
        assert len(analysis.results) == 10


class TestSerpAnalysisModel:
    """Test SerpAnalysis model."""
    
    def test_serp_analysis_creation(self):
        """Test creating a SerpAnalysis object."""
        results = [
            SerpResult(rank=i, url=f"https://example{i}.com", title=f"Title {i}", snippet=f"Snippet {i}")
            for i in range(1, 6)
        ]
        
        analysis = SerpAnalysis(
            keyword="test keyword",
            total_results=5,
            results=results,
            common_themes=["theme1", "theme2"],
            primary_keywords=["keyword1"],
            secondary_keywords=["keyword2", "keyword3"]
        )
        
        assert analysis.keyword == "test keyword"
        assert analysis.total_results == 5
        assert len(analysis.results) == 5
        assert len(analysis.common_themes) == 2
