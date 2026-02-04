"""Tests for SEO validation."""
import pytest

from app.models.article import (
    GeneratedArticle, ArticleSection, HeadingLevel,
    SEOMetadata, KeywordAnalysis, InternalLink, 
    ExternalReference, FAQItem
)
from app.utils.validators import (
    validate_heading_hierarchy,
    validate_keyword_placement,
    validate_word_count,
    validate_meta_lengths,
    validate_content_structure,
    run_all_validations
)


@pytest.fixture
def valid_article():
    """Create a valid article for testing."""
    return GeneratedArticle(
        title="Best Productivity Tools for Remote Teams in 2025",
        introduction="Productivity tools are essential for remote teams. " * 10,  # ~60 words
        sections=[
            ArticleSection(
                heading="Project Management Tools",
                heading_level=HeadingLevel.H2,
                content="Content about project management. " * 50,  # ~200 words
                subsections=[
                    ArticleSection(
                        heading="Popular Options",
                        heading_level=HeadingLevel.H3,
                        content="Details about popular tools. " * 25  # ~100 words
                    )
                ]
            ),
            ArticleSection(
                heading="Communication Apps",
                heading_level=HeadingLevel.H2,
                content="Communication is key for remote work. " * 50
            ),
            ArticleSection(
                heading="Time Tracking Solutions",
                heading_level=HeadingLevel.H2,
                content="Time tracking helps teams stay on track. " * 50
            ),
            ArticleSection(
                heading="Collaboration Platforms",
                heading_level=HeadingLevel.H2,
                content="Collaboration platforms bring teams together. " * 50
            )
        ],
        conclusion="In conclusion, productivity tools matter for remote teams. " * 5,
        faq_section=[
            FAQItem(question="What is the best tool?", answer="It depends on your needs."),
            FAQItem(question="How much do they cost?", answer="Prices vary widely.")
        ],
        seo_metadata=SEOMetadata(
            title_tag="Best Productivity Tools 2025",
            meta_description="Discover the best productivity tools for remote teams in 2025.",
            primary_keyword="productivity tools"
        ),
        keyword_analysis=KeywordAnalysis(
            primary_keyword="productivity tools",
            primary_keyword_count=10,
            primary_keyword_density=1.5,
            keyword_in_title=True,
            keyword_in_intro=True,
            keyword_in_headings=2
        ),
        internal_links=[
            InternalLink(anchor_text="project management", target_topic="PM Guide", context="Learn more"),
            InternalLink(anchor_text="remote work tips", target_topic="Remote Tips", context="Check out"),
            InternalLink(anchor_text="team productivity", target_topic="Productivity Guide", context="Read more")
        ],
        external_references=[
            ExternalReference(source_name="Forbes", source_url="https://forbes.com", source_type="article", citation_context="Stats", suggested_placement="Introduction"),
            ExternalReference(source_name="HBR", source_url="https://hbr.org", source_type="study", citation_context="Research", suggested_placement="Section 1")
        ],
        total_word_count=1500
    )


class TestHeadingHierarchy:
    """Test heading hierarchy validation."""
    
    def test_valid_heading_hierarchy(self, valid_article):
        """Test valid heading structure passes."""
        is_valid, issues = validate_heading_hierarchy(valid_article)
        assert is_valid is True
        assert len(issues) == 0
    
    def test_missing_sections(self):
        """Test article without sections has no hierarchy issues but structure issues."""
        article = GeneratedArticle(
            title="Test",
            introduction="Test intro",
            sections=[],
            conclusion="Test conclusion",
            faq_section=[],
            seo_metadata=SEOMetadata(
                title_tag="Test",
                meta_description="Test",
                primary_keyword="test"
            ),
            keyword_analysis=KeywordAnalysis(primary_keyword="test")
        )
        
        # Empty sections means no heading hierarchy violations (nothing to check)
        is_valid, issues = validate_heading_hierarchy(article)
        assert is_valid is True  # No violations since no sections
        
        # But content structure validation catches missing sections
        structure_valid, details = validate_content_structure(article)
        assert structure_valid is False
        assert details["has_sections"] is False


class TestKeywordPlacement:
    """Test keyword placement validation."""
    
    def test_valid_keyword_placement(self, valid_article):
        """Test valid keyword placement passes."""
        is_valid, placements = validate_keyword_placement(
            valid_article,
            "productivity tools"
        )
        
        assert is_valid is True
        assert placements["in_title"] is True
        assert placements["in_introduction"] is True
    
    def test_missing_keyword_in_title(self):
        """Test missing keyword in title fails."""
        article = GeneratedArticle(
            title="Remote Work Guide",  # No keyword
            introduction="Productivity tools are essential.",
            sections=[],
            conclusion="The end.",
            faq_section=[],
            seo_metadata=SEOMetadata(
                title_tag="Remote Work",
                meta_description="A guide to remote work with productivity tools",
                primary_keyword="productivity tools"
            ),
            keyword_analysis=KeywordAnalysis(primary_keyword="productivity tools")
        )
        
        is_valid, placements = validate_keyword_placement(article, "productivity tools")
        
        assert is_valid is False
        assert placements["in_title"] is False


class TestWordCount:
    """Test word count validation."""
    
    def test_valid_word_count(self, valid_article):
        """Test word count within tolerance passes."""
        valid_article.total_word_count = 1500
        
        is_valid, details = validate_word_count(valid_article, target=1500)
        
        assert is_valid is True
        assert details["deviation_percent"] == 0
    
    def test_word_count_too_low(self, valid_article):
        """Test word count below tolerance fails."""
        valid_article.total_word_count = 1000
        
        is_valid, details = validate_word_count(valid_article, target=1500)
        
        assert is_valid is False
        assert details["actual"] < details["min_acceptable"]
    
    def test_word_count_too_high(self, valid_article):
        """Test word count above tolerance fails."""
        valid_article.total_word_count = 2000
        
        is_valid, details = validate_word_count(valid_article, target=1500)
        
        assert is_valid is False
        assert details["actual"] > details["max_acceptable"]


class TestMetaLengths:
    """Test meta tag length validation."""
    
    def test_valid_meta_lengths(self, valid_article):
        """Test valid meta lengths pass."""
        is_valid, details = validate_meta_lengths(valid_article)
        
        assert is_valid is True
        assert details["title_tag_valid"] is True
        assert details["meta_description_valid"] is True
    
    def test_title_too_long(self):
        """Test title tag over 60 chars fails validation check."""
        # Create article with valid SEOMetadata first
        article = GeneratedArticle(
            title="Test",
            introduction="Test",
            sections=[],
            conclusion="Test",
            faq_section=[],
            seo_metadata=SEOMetadata(
                title_tag="Short title",
                meta_description="Valid description",
                primary_keyword="test"
            ),
            keyword_analysis=KeywordAnalysis(primary_keyword="test")
        )
        
        # Manually override the title_tag to bypass Pydantic validation for testing
        # This simulates a scenario where we need to validate external data
        object.__setattr__(article.seo_metadata, 'title_tag', 'A' * 70)
        
        is_valid, details = validate_meta_lengths(article)
        
        assert is_valid is False
        assert details["title_tag_valid"] is False


class TestContentStructure:
    """Test content structure validation."""
    
    def test_valid_structure(self, valid_article):
        """Test valid structure passes."""
        is_valid, details = validate_content_structure(valid_article)
        
        assert is_valid is True
        assert details["has_sections"] is True
        assert details["has_enough_internal_links"] is True
        assert details["has_enough_external_refs"] is True
    
    def test_not_enough_sections(self):
        """Test too few sections fails."""
        article = GeneratedArticle(
            title="Test",
            introduction="Test",
            sections=[
                ArticleSection(heading="One", heading_level=HeadingLevel.H2, content="Only one section")
            ],
            conclusion="Test",
            faq_section=[],
            seo_metadata=SEOMetadata(title_tag="Test", meta_description="Test", primary_keyword="test"),
            keyword_analysis=KeywordAnalysis(primary_keyword="test"),
            internal_links=[
                InternalLink(anchor_text="a", target_topic="A", context="x"),
                InternalLink(anchor_text="b", target_topic="B", context="y"),
                InternalLink(anchor_text="c", target_topic="C", context="z")
            ],
            external_references=[
                ExternalReference(source_name="A", source_url="a", source_type="x", citation_context="y", suggested_placement="z"),
                ExternalReference(source_name="B", source_url="b", source_type="x", citation_context="y", suggested_placement="z")
            ]
        )
        
        is_valid, details = validate_content_structure(article)
        
        assert is_valid is False
        assert details["has_sections"] is False


class TestRunAllValidations:
    """Test complete validation run."""
    
    def test_all_validations(self, valid_article):
        """Test running all validations."""
        result = run_all_validations(valid_article, target_word_count=1500)
        
        assert "overall_valid" in result
        assert "validations" in result
        assert "heading_hierarchy" in result["validations"]
        assert "keyword_placement" in result["validations"]
        assert "word_count" in result["validations"]
        assert "meta_tags" in result["validations"]
        assert "content_structure" in result["validations"]
