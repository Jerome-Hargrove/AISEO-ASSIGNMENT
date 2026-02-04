"""Article and SEO content data models."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class HeadingLevel(str, Enum):
    """Heading hierarchy levels."""
    H1 = "h1"
    H2 = "h2"
    H3 = "h3"


class ArticleSection(BaseModel):
    """A section of the article with heading and content."""
    
    heading: str = Field(..., description="Section heading text")
    heading_level: HeadingLevel = Field(..., description="Heading level (H1, H2, H3)")
    content: str = Field(..., description="Section body content")
    word_count: int = Field(default=0, description="Word count of this section")
    subsections: List["ArticleSection"] = Field(default_factory=list, description="Nested subsections")
    
    def calculate_word_count(self) -> int:
        """Calculate total word count including subsections."""
        count = len(self.content.split())
        for subsection in self.subsections:
            count += subsection.calculate_word_count()
        return count


class SEOMetadata(BaseModel):
    """SEO metadata for the article."""
    
    title_tag: str = Field(..., max_length=60, description="SEO title tag (max 60 chars)")
    meta_description: str = Field(..., max_length=160, description="Meta description (max 160 chars)")
    primary_keyword: str = Field(..., description="Primary target keyword")
    secondary_keywords: List[str] = Field(default_factory=list, description="Secondary keywords used")
    keyword_density: Optional[float] = Field(None, description="Primary keyword density percentage")


class KeywordAnalysis(BaseModel):
    """Analysis of keywords used in the article."""
    
    primary_keyword: str = Field(..., description="Primary target keyword")
    primary_keyword_count: int = Field(default=0, description="Times primary keyword appears")
    primary_keyword_density: float = Field(default=0.0, description="Density as percentage")
    secondary_keywords: Dict[str, int] = Field(default_factory=dict, description="Secondary keyword counts")
    keyword_in_title: bool = Field(default=False, description="Primary keyword in title")
    keyword_in_intro: bool = Field(default=False, description="Primary keyword in introduction")
    keyword_in_headings: int = Field(default=0, description="Primary keyword in headings count")


class InternalLink(BaseModel):
    """Internal linking suggestion."""
    
    anchor_text: str = Field(..., description="Suggested anchor text for the link")
    target_topic: str = Field(..., description="Suggested target page/topic to link to")
    context: str = Field(..., description="Context/sentence where link should be placed")
    placement_section: Optional[str] = Field(None, description="Which section to place the link in")


class ExternalReference(BaseModel):
    """External reference/citation suggestion."""
    
    source_name: str = Field(..., description="Name of the authoritative source")
    source_url: str = Field(..., description="URL of the source")
    source_type: str = Field(default="article", description="Type: article, study, report, etc.")
    citation_context: str = Field(..., description="What information to cite from this source")
    suggested_placement: str = Field(..., description="Where in the article to place this citation")


class FAQItem(BaseModel):
    """FAQ question and answer pair."""
    
    question: str = Field(..., description="The question")
    answer: str = Field(..., description="The answer")


class ArticleOutline(BaseModel):
    """Structured outline for article generation."""
    
    title: str = Field(..., description="Article title (H1)")
    introduction_points: List[str] = Field(default_factory=list, description="Key points for introduction")
    sections: List[Dict[str, Any]] = Field(default_factory=list, description="Planned sections with subtopics")
    conclusion_points: List[str] = Field(default_factory=list, description="Key points for conclusion")
    faq_questions: List[str] = Field(default_factory=list, description="FAQ questions to answer")


class GeneratedArticle(BaseModel):
    """Complete generated article with all SEO components."""
    
    # Core content
    title: str = Field(..., description="Article title (H1)")
    sections: List[ArticleSection] = Field(default_factory=list, description="Article sections")
    introduction: str = Field(..., description="Article introduction paragraph")
    conclusion: str = Field(..., description="Article conclusion paragraph")
    faq_section: List[FAQItem] = Field(default_factory=list, description="FAQ section")
    
    # SEO components
    seo_metadata: SEOMetadata = Field(..., description="SEO metadata")
    keyword_analysis: KeywordAnalysis = Field(..., description="Keyword usage analysis")
    
    # Linking suggestions
    internal_links: List[InternalLink] = Field(default_factory=list, description="Internal link suggestions")
    external_references: List[ExternalReference] = Field(default_factory=list, description="External citations")
    
    # Metrics
    total_word_count: int = Field(default=0, description="Total article word count")
    reading_time_minutes: int = Field(default=0, description="Estimated reading time")
    
    def calculate_metrics(self) -> None:
        """Calculate word count and reading time."""
        word_count = len(self.introduction.split()) + len(self.conclusion.split())
        for section in self.sections:
            word_count += section.calculate_word_count()
        for faq in self.faq_section:
            word_count += len(faq.answer.split())
        
        self.total_word_count = word_count
        self.reading_time_minutes = max(1, word_count // 200)  # Average reading speed
    
    def to_markdown(self) -> str:
        """Convert article to markdown format."""
        lines = []
        lines.append(f"# {self.title}\n")
        lines.append(f"{self.introduction}\n")
        
        for section in self.sections:
            lines.append(self._section_to_markdown(section))
        
        lines.append(f"{self.conclusion}\n")
        
        if self.faq_section:
            lines.append("## Frequently Asked Questions\n")
            for faq in self.faq_section:
                lines.append(f"### {faq.question}\n")
                lines.append(f"{faq.answer}\n")
        
        return "\n".join(lines)
    
    def _section_to_markdown(self, section: ArticleSection, depth: int = 0) -> str:
        """Convert a section to markdown recursively."""
        prefix = "#" * (2 + depth)  # H2 for top-level sections
        lines = [f"{prefix} {section.heading}\n", f"{section.content}\n"]
        
        for subsection in section.subsections:
            lines.append(self._section_to_markdown(subsection, depth + 1))
        
        return "\n".join(lines)


# Enable forward references
ArticleSection.model_rebuild()
