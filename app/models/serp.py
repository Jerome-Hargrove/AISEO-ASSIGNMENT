"""SERP (Search Engine Results Page) data models."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SerpResult(BaseModel):
    """Individual search result from SERP data."""
    
    rank: int = Field(..., ge=1, le=100, description="Position in search results")
    url: str = Field(..., description="URL of the result")
    title: str = Field(..., description="Title of the result page")
    snippet: str = Field(..., description="Description snippet from search results")
    domain: Optional[str] = Field(None, description="Domain extracted from URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "url": "https://example.com/productivity-tools",
                "title": "15 Best Productivity Tools for Remote Teams in 2025",
                "snippet": "Discover the top productivity tools that help remote teams collaborate..."
            }
        }


class ExtractedTopic(BaseModel):
    """A topic or subtopic extracted from SERP analysis."""
    
    topic: str = Field(..., description="The topic or subtopic name")
    frequency: int = Field(default=1, description="How many results cover this topic")
    importance: str = Field(default="medium", description="Importance level: high, medium, low")


class ExtractedQuestion(BaseModel):
    """A question extracted from search results for FAQ generation."""
    
    question: str = Field(..., description="The question text")
    source: str = Field(default="serp", description="Where the question was found")


class SerpAnalysis(BaseModel):
    """Aggregated analysis of SERP results."""
    
    keyword: str = Field(..., description="The primary keyword searched")
    total_results: int = Field(..., description="Number of results analyzed")
    results: List[SerpResult] = Field(default_factory=list, description="Raw SERP results")
    
    # Extracted insights
    common_themes: List[str] = Field(default_factory=list, description="Common themes across results")
    topics: List[ExtractedTopic] = Field(default_factory=list, description="Topics and subtopics identified")
    primary_keywords: List[str] = Field(default_factory=list, description="Primary keywords identified")
    secondary_keywords: List[str] = Field(default_factory=list, description="Secondary/related keywords")
    questions: List[ExtractedQuestion] = Field(default_factory=list, description="Questions for FAQ section")
    
    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "keyword": "best productivity tools for remote teams",
                "total_results": 10,
                "common_themes": ["collaboration", "time management", "communication"],
                "topics": [
                    {"topic": "Project Management Tools", "frequency": 8, "importance": "high"},
                    {"topic": "Communication Platforms", "frequency": 7, "importance": "high"}
                ],
                "primary_keywords": ["productivity tools", "remote teams"],
                "secondary_keywords": ["collaboration software", "team management"]
            }
        }
