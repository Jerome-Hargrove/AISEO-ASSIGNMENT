"""Outline generator service for creating SEO-optimized article structures."""
import logging
from typing import List, Dict, Any

from app.models.serp import SerpAnalysis
from app.models.article import ArticleOutline
from app.utils.llm_client import llm_client

logger = logging.getLogger(__name__)


class OutlineGenerator:
    """Generate article outlines from SERP analysis."""
    
    async def generate_outline(
        self,
        serp_analysis: SerpAnalysis,
        target_word_count: int = 1500
    ) -> ArticleOutline:
        """Generate an SEO-optimized article outline.
        
        Args:
            serp_analysis: Analyzed SERP data
            target_word_count: Target word count for the article
        
        Returns:
            ArticleOutline with structured sections
        """
        # Prepare context from SERP analysis
        themes = ", ".join(serp_analysis.common_themes[:5]) if serp_analysis.common_themes else "general"
        topics = "\n".join([
            f"- {t.topic} (importance: {t.importance})"
            for t in serp_analysis.topics[:8]
        ])
        keywords = ", ".join(serp_analysis.primary_keywords[:5])
        secondary_kws = ", ".join(serp_analysis.secondary_keywords[:10])
        questions = "\n".join([
            f"- {q.question}" for q in serp_analysis.questions[:5]
        ])
        
        # Top competing articles for reference
        competing_titles = "\n".join([
            f"- {r.title}" for r in serp_analysis.results[:5]
        ])
        
        prompt = f"""Create an SEO-optimized article outline for the keyword: "{serp_analysis.keyword}"

TARGET: {target_word_count} words

COMPETITIVE ANALYSIS:
Top ranking articles:
{competing_titles}

Common themes: {themes}

Topics to cover:
{topics}

Primary keywords: {keywords}
Secondary keywords: {secondary_kws}

Common questions users have:
{questions}

Create an outline that:
1. Has an engaging, keyword-rich title
2. Covers all important topics from the competition
3. Has a logical H1 > H2 > H3 structure
4. Includes 4-6 main sections
5. Has an introduction that hooks readers
6. Has a conclusion that summarizes key points
7. Includes FAQ questions to answer

Return JSON with:
{{
    "title": "SEO-optimized title with primary keyword",
    "introduction_points": ["key point 1", "key point 2", "key point 3"],
    "sections": [
        {{
            "heading": "H2 Section Title",
            "key_points": ["point 1", "point 2"],
            "subsections": [
                {{"heading": "H3 Subsection", "key_points": ["point"]}}
            ]
        }}
    ],
    "conclusion_points": ["summary point 1", "summary point 2"],
    "faq_questions": ["question 1?", "question 2?", "question 3?"]
}}"""

        try:
            outline_data = await llm_client.generate_json(
                system_prompt="You are an expert SEO content strategist. Create article outlines that rank well and engage readers. Return only valid JSON.",
                user_prompt=prompt,
                temperature=0.5
            )
            
            return ArticleOutline(
                title=outline_data.get("title", f"Complete Guide to {serp_analysis.keyword}"),
                introduction_points=outline_data.get("introduction_points", []),
                sections=outline_data.get("sections", []),
                conclusion_points=outline_data.get("conclusion_points", []),
                faq_questions=outline_data.get("faq_questions", [])
            )
            
        except Exception as e:
            logger.error(f"Error generating outline: {str(e)}")
            # Return a basic fallback outline
            return self._create_fallback_outline(serp_analysis)
    
    def _create_fallback_outline(self, serp_analysis: SerpAnalysis) -> ArticleOutline:
        """Create a basic outline when LLM fails."""
        sections = []
        for i, topic in enumerate(serp_analysis.topics[:5], start=1):
            sections.append({
                "heading": topic.topic,
                "key_points": [f"Discuss {topic.topic.lower()}"],
                "subsections": []
            })
        
        return ArticleOutline(
            title=f"Complete Guide to {serp_analysis.keyword.title()}",
            introduction_points=[
                f"Overview of {serp_analysis.keyword}",
                "Why this topic matters",
                "What you'll learn"
            ],
            sections=sections,
            conclusion_points=[
                "Summary of key points",
                "Final recommendations"
            ],
            faq_questions=[q.question for q in serp_analysis.questions[:3]]
        )


# Singleton instance
outline_generator = OutlineGenerator()
