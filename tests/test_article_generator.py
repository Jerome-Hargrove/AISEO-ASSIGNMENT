"""Tests for article generator service."""
import pytest
from unittest.mock import AsyncMock, patch

from app.models.serp import SerpAnalysis, SerpResult, ExtractedTopic, ExtractedQuestion
from app.models.article import (
    ArticleOutline, ArticleSection, HeadingLevel,
    GeneratedArticle, SEOMetadata, KeywordAnalysis
)
from app.services.article_generator import ArticleGenerator


@pytest.fixture
def sample_serp_analysis():
    """Create sample SERP analysis for testing."""
    return SerpAnalysis(
        keyword="best productivity tools",
        total_results=10,
        results=[
            SerpResult(rank=i, url=f"https://example{i}.com", title=f"Article {i}", snippet=f"Snippet {i}")
            for i in range(1, 11)
        ],
        common_themes=["automation", "collaboration", "time management"],
        topics=[
            ExtractedTopic(topic="Project Management Tools", frequency=8, importance="high"),
            ExtractedTopic(topic="Communication Apps", frequency=7, importance="high"),
            ExtractedTopic(topic="Time Tracking", frequency=5, importance="medium"),
        ],
        primary_keywords=["productivity tools", "remote teams"],
        secondary_keywords=["collaboration software", "team apps", "workflow automation"],
        questions=[
            ExtractedQuestion(question="What are the best productivity tools?", source="serp"),
            ExtractedQuestion(question="How to improve team productivity?", source="serp"),
        ]
    )


@pytest.fixture
def sample_outline():
    """Create sample outline for testing."""
    return ArticleOutline(
        title="10 Best Productivity Tools for Remote Teams in 2025",
        introduction_points=["Importance of productivity", "Challenge of remote work"],
        sections=[
            {
                "heading": "Project Management Tools",
                "key_points": ["Task organization", "Team collaboration"],
                "subsections": []
            },
            {
                "heading": "Communication Apps",
                "key_points": ["Video conferencing", "Instant messaging"],
                "subsections": []
            }
        ],
        conclusion_points=["Summary", "Recommendations"],
        faq_questions=["What is the best tool?", "How to choose?"]
    )


@pytest.fixture
def article_generator():
    """Create ArticleGenerator instance."""
    return ArticleGenerator()


class TestArticleGenerator:
    """Test suite for article generator."""
    
    @pytest.mark.asyncio
    async def test_generate_introduction(self, article_generator, sample_outline):
        """Test introduction generation."""
        with patch('app.services.article_generator.llm_client') as mock_llm:
            mock_llm.generate_completion = AsyncMock(
                return_value="Productivity tools have become essential for remote teams..."
            )
            
            intro = await article_generator._generate_introduction(
                sample_outline,
                "productivity tools",
                ["remote work", "collaboration"]
            )
        
        assert isinstance(intro, str)
        assert len(intro) > 0
    
    @pytest.mark.asyncio
    async def test_generate_section(self, article_generator):
        """Test section generation."""
        section_outline = {
            "heading": "Project Management Tools",
            "key_points": ["Task tracking", "Team coordination"],
            "subsections": []
        }
        
        with patch('app.services.article_generator.llm_client') as mock_llm:
            mock_llm.generate_completion = AsyncMock(
                return_value="Project management tools help teams stay organized..."
            )
            
            section = await article_generator._generate_section(
                section_outline,
                "productivity tools",
                ["project management"],
                300
            )
        
        assert isinstance(section, ArticleSection)
        assert section.heading == "Project Management Tools"
        assert section.heading_level == HeadingLevel.H2
    
    def test_analyze_keywords(self, article_generator):
        """Test keyword analysis."""
        # Create a mock article
        sections = [
            ArticleSection(
                heading="Section About Productivity Tools",
                heading_level=HeadingLevel.H2,
                content="Productivity tools are essential. The best productivity tools help teams work better."
            )
        ]
        
        article = GeneratedArticle(
            title="Best Productivity Tools Guide",
            introduction="Productivity tools have become essential for modern teams.",
            sections=sections,
            conclusion="In conclusion, productivity tools matter.",
            faq_section=[],
            seo_metadata=SEOMetadata(
                title_tag="Best Productivity Tools",
                meta_description="Guide to productivity tools",
                primary_keyword="productivity tools"
            ),
            keyword_analysis=KeywordAnalysis(primary_keyword="productivity tools")
        )
        
        analysis = article_generator._analyze_keywords(
            article,
            "productivity tools",
            ["collaboration", "team work"]
        )
        
        assert analysis.primary_keyword == "productivity tools"
        assert analysis.keyword_in_title is True
        assert analysis.keyword_in_intro is True
        assert analysis.primary_keyword_count > 0


class TestArticleSection:
    """Test ArticleSection model."""
    
    def test_calculate_word_count(self):
        """Test word count calculation."""
        section = ArticleSection(
            heading="Test Section",
            heading_level=HeadingLevel.H2,
            content="This is a test section with ten words in it."
        )
        
        count = section.calculate_word_count()
        assert count == 10
    
    def test_calculate_word_count_with_subsections(self):
        """Test word count with nested subsections."""
        section = ArticleSection(
            heading="Parent Section",
            heading_level=HeadingLevel.H2,
            content="Parent content here.",  # 3 words
            subsections=[
                ArticleSection(
                    heading="Child Section",
                    heading_level=HeadingLevel.H3,
                    content="Child content is here too."  # 5 words
                )
            ]
        )
        
        count = section.calculate_word_count()
        assert count == 8


class TestGeneratedArticle:
    """Test GeneratedArticle model."""
    
    def test_calculate_metrics(self):
        """Test metrics calculation."""
        article = GeneratedArticle(
            title="Test Article",
            introduction="This is the introduction.",  # 4 words
            sections=[
                ArticleSection(
                    heading="Section 1",
                    heading_level=HeadingLevel.H2,
                    content="Section one content here."  # 4 words
                )
            ],
            conclusion="This is the conclusion.",  # 4 words
            faq_section=[],
            seo_metadata=SEOMetadata(
                title_tag="Test",
                meta_description="Test description",
                primary_keyword="test"
            ),
            keyword_analysis=KeywordAnalysis(primary_keyword="test")
        )
        
        article.calculate_metrics()
        
        assert article.total_word_count == 12
        assert article.reading_time_minutes >= 1
    
    def test_to_markdown(self):
        """Test markdown conversion."""
        article = GeneratedArticle(
            title="Test Article Title",
            introduction="Introduction paragraph here.",
            sections=[
                ArticleSection(
                    heading="First Section",
                    heading_level=HeadingLevel.H2,
                    content="First section content."
                )
            ],
            conclusion="Conclusion paragraph.",
            faq_section=[],
            seo_metadata=SEOMetadata(
                title_tag="Test",
                meta_description="Test",
                primary_keyword="test"
            ),
            keyword_analysis=KeywordAnalysis(primary_keyword="test")
        )
        
        markdown = article.to_markdown()
        
        assert "# Test Article Title" in markdown
        assert "## First Section" in markdown
        assert "Introduction paragraph here." in markdown
        assert "Conclusion paragraph." in markdown
