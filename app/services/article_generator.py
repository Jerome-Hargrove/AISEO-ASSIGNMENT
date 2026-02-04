"""Article generator service for creating SEO-optimized content."""
import logging
import re
from typing import List, Dict, Any

from app.models.serp import SerpAnalysis
from app.models.article import (
    ArticleOutline, ArticleSection, HeadingLevel, 
    SEOMetadata, KeywordAnalysis, InternalLink, 
    ExternalReference, FAQItem, GeneratedArticle
)
from app.utils.llm_client import llm_client

logger = logging.getLogger(__name__)


class ArticleGenerator:
    """Generate full SEO-optimized articles from outlines."""
    
    async def generate_article(
        self,
        outline: ArticleOutline,
        serp_analysis: SerpAnalysis,
        target_word_count: int = 1500
    ) -> GeneratedArticle:
        """Generate a complete SEO-optimized article.
        
        Args:
            outline: Article outline to follow
            serp_analysis: SERP analysis data for SEO context
            target_word_count: Target word count
        
        Returns:
            Complete GeneratedArticle
        """
        primary_keyword = serp_analysis.keyword
        secondary_keywords = serp_analysis.secondary_keywords[:10]
        
        # Generate each part of the article
        introduction = await self._generate_introduction(
            outline, primary_keyword, secondary_keywords
        )
        
        sections = await self._generate_sections(
            outline, primary_keyword, secondary_keywords, target_word_count
        )
        
        conclusion = await self._generate_conclusion(
            outline, primary_keyword
        )
        
        faq_section = await self._generate_faq(
            outline.faq_questions, primary_keyword
        )
        
        # Generate SEO metadata
        seo_metadata = await self._generate_seo_metadata(
            outline.title, primary_keyword, introduction
        )
        
        # Generate linking suggestions
        internal_links = await self._generate_internal_links(
            primary_keyword, secondary_keywords
        )
        
        external_references = await self._generate_external_references(
            serp_analysis
        )
        
        # Build the article
        article = GeneratedArticle(
            title=outline.title,
            introduction=introduction,
            sections=sections,
            conclusion=conclusion,
            faq_section=faq_section,
            seo_metadata=seo_metadata,
            keyword_analysis=KeywordAnalysis(
                primary_keyword=primary_keyword,
                secondary_keywords={}
            ),
            internal_links=internal_links,
            external_references=external_references
        )
        
        # Calculate metrics and keyword analysis
        article.calculate_metrics()
        article.keyword_analysis = self._analyze_keywords(
            article, primary_keyword, secondary_keywords
        )
        
        return article
    
    async def _generate_introduction(
        self,
        outline: ArticleOutline,
        primary_keyword: str,
        secondary_keywords: List[str]
    ) -> str:
        """Generate engaging introduction with primary keyword."""
        points = "\n".join([f"- {p}" for p in outline.introduction_points])
        keywords_str = ", ".join(secondary_keywords[:5])
        
        prompt = f"""Write an engaging introduction paragraph for an article titled: "{outline.title}"

Primary keyword (MUST appear naturally in first 100 words): {primary_keyword}
Related keywords to weave in: {keywords_str}

Key points to cover:
{points}

Requirements:
- 150-200 words
- Hook the reader immediately
- Include primary keyword in the first sentence if possible
- Set expectations for what the article covers
- Be conversational but professional
- Don't use phrases like "In this article" or "Today we'll discuss"

Return only the introduction paragraph, no headers."""

        try:
            introduction = await llm_client.generate_completion(
                system_prompt="You are an expert content writer who creates engaging, SEO-friendly content that reads naturally.",
                user_prompt=prompt,
                temperature=0.7
            )
            return introduction.strip()
        except Exception as e:
            logger.error(f"Error generating introduction: {str(e)}")
            return f"{primary_keyword.title()} is an essential topic for anyone looking to succeed in today's competitive landscape. In this comprehensive guide, we'll explore everything you need to know to make informed decisions and achieve your goals."
    
    async def _generate_sections(
        self,
        outline: ArticleOutline,
        primary_keyword: str,
        secondary_keywords: List[str],
        target_word_count: int
    ) -> List[ArticleSection]:
        """Generate all article sections."""
        sections = []
        num_sections = len(outline.sections)
        words_per_section = (target_word_count - 400) // max(num_sections, 1)  # Reserve for intro/conclusion
        
        for section_outline in outline.sections:
            section = await self._generate_section(
                section_outline,
                primary_keyword,
                secondary_keywords,
                words_per_section
            )
            sections.append(section)
        
        return sections
    
    async def _generate_section(
        self,
        section_outline: Dict[str, Any],
        primary_keyword: str,
        secondary_keywords: List[str],
        target_words: int
    ) -> ArticleSection:
        """Generate a single section with potential subsections."""
        heading = section_outline.get("heading", "")
        key_points = section_outline.get("key_points", [])
        subsections_outline = section_outline.get("subsections", [])
        
        points_str = "\n".join([f"- {p}" for p in key_points])
        keywords_str = ", ".join(secondary_keywords[:3])
        
        prompt = f"""Write a section for an article about "{primary_keyword}".

Section heading: {heading}

Key points to cover:
{points_str}

Related keywords to include naturally: {keywords_str}

Requirements:
- {target_words} words approximately
- Use clear, professional language
- Include specific examples or data when relevant
- Be informative and actionable
- Vary sentence structure
- Don't use the section heading in the content

Return only the section content, no headers."""

        try:
            content = await llm_client.generate_completion(
                system_prompt="You are an expert content writer creating informative, engaging content.",
                user_prompt=prompt,
                temperature=0.7
            )
            
            # Generate subsections if any
            subsections = []
            for sub_outline in subsections_outline:
                sub_section = await self._generate_section(
                    sub_outline,
                    primary_keyword,
                    secondary_keywords,
                    target_words // 2
                )
                sub_section.heading_level = HeadingLevel.H3
                subsections.append(sub_section)
            
            section = ArticleSection(
                heading=heading,
                heading_level=HeadingLevel.H2,
                content=content.strip(),
                subsections=subsections
            )
            section.word_count = section.calculate_word_count()
            
            return section
            
        except Exception as e:
            logger.error(f"Error generating section '{heading}': {str(e)}")
            return ArticleSection(
                heading=heading,
                heading_level=HeadingLevel.H2,
                content=f"This section covers important aspects of {heading.lower()} in relation to {primary_keyword}.",
                subsections=[]
            )
    
    async def _generate_conclusion(
        self,
        outline: ArticleOutline,
        primary_keyword: str
    ) -> str:
        """Generate article conclusion."""
        points = "\n".join([f"- {p}" for p in outline.conclusion_points])
        
        prompt = f"""Write a conclusion for an article about "{primary_keyword}".

Key points to summarize:
{points}

Requirements:
- 100-150 words
- Summarize key takeaways
- Include a call to action
- End on an inspiring or forward-looking note
- Include the primary keyword naturally

Return only the conclusion paragraph."""

        try:
            conclusion = await llm_client.generate_completion(
                system_prompt="You are an expert content writer who creates compelling conclusions.",
                user_prompt=prompt,
                temperature=0.7
            )
            return conclusion.strip()
        except Exception as e:
            logger.error(f"Error generating conclusion: {str(e)}")
            return f"In conclusion, understanding {primary_keyword} is crucial for success. By applying the strategies and insights shared in this guide, you'll be well-equipped to achieve your goals. Take action today and start implementing these principles."
    
    async def _generate_faq(
        self,
        questions: List[str],
        primary_keyword: str
    ) -> List[FAQItem]:
        """Generate FAQ section."""
        if not questions:
            return []
        
        faq_items = []
        for question in questions[:5]:
            prompt = f"""Answer this question about "{primary_keyword}":

Question: {question}

Requirements:
- 50-100 words
- Be direct and informative
- Include relevant details
- Be accurate and helpful

Return only the answer."""

            try:
                answer = await llm_client.generate_completion(
                    system_prompt="You are a helpful expert answering FAQs clearly and concisely.",
                    user_prompt=prompt,
                    temperature=0.5
                )
                
                faq_items.append(FAQItem(
                    question=question,
                    answer=answer.strip()
                ))
            except Exception as e:
                logger.error(f"Error generating FAQ for '{question}': {str(e)}")
        
        return faq_items
    
    async def _generate_seo_metadata(
        self,
        title: str,
        primary_keyword: str,
        introduction: str
    ) -> SEOMetadata:
        """Generate SEO metadata."""
        prompt = f"""Create SEO metadata for an article.

Title: {title}
Primary keyword: {primary_keyword}
Introduction: {introduction[:300]}

Return JSON with:
{{
    "title_tag": "SEO title tag (max 60 characters, include keyword)",
    "meta_description": "Compelling meta description (max 155 characters, include keyword)"
}}"""

        try:
            meta_data = await llm_client.generate_json(
                system_prompt="You are an SEO expert creating optimized metadata.",
                user_prompt=prompt,
                temperature=0.3
            )
            
            title_tag = meta_data.get("title_tag", title)[:60]
            meta_desc = meta_data.get("meta_description", introduction[:155])[:160]
            
            return SEOMetadata(
                title_tag=title_tag,
                meta_description=meta_desc,
                primary_keyword=primary_keyword,
                secondary_keywords=[]
            )
        except Exception as e:
            logger.error(f"Error generating SEO metadata: {str(e)}")
            return SEOMetadata(
                title_tag=title[:60],
                meta_description=introduction[:155],
                primary_keyword=primary_keyword,
                secondary_keywords=[]
            )
    
    async def _generate_internal_links(
        self,
        primary_keyword: str,
        secondary_keywords: List[str]
    ) -> List[InternalLink]:
        """Generate internal linking suggestions."""
        keywords_str = ", ".join(secondary_keywords[:10])
        
        prompt = f"""Suggest 4 internal linking opportunities for an article about "{primary_keyword}".

Related keywords: {keywords_str}

For each suggestion, provide:
- Anchor text (the clickable link text)
- Target topic (what page/article to link to)
- Context (example sentence where the link would appear)

Return JSON array:
[
    {{
        "anchor_text": "example anchor",
        "target_topic": "Related Article Topic",
        "context": "This is an example sentence with the anchor text as a link."
    }}
]"""

        try:
            links_data = await llm_client.generate_json(
                system_prompt="You are an SEO expert suggesting internal linking strategies.",
                user_prompt=prompt,
                temperature=0.5
            )
            
            links = []
            for link in links_data[:5] if isinstance(links_data, list) else []:
                links.append(InternalLink(
                    anchor_text=link.get("anchor_text", ""),
                    target_topic=link.get("target_topic", ""),
                    context=link.get("context", ""),
                    placement_section=None
                ))
            return links
        except Exception as e:
            logger.error(f"Error generating internal links: {str(e)}")
            return []
    
    async def _generate_external_references(
        self,
        serp_analysis: SerpAnalysis
    ) -> List[ExternalReference]:
        """Generate external reference suggestions."""
        # Use top-ranking authoritative sources from SERP
        authoritative_domains = ["forbes.com", "harvard.edu", "gov", "edu", "statista.com", "mckinsey.com"]
        
        references = []
        for result in serp_analysis.results[:10]:
            domain = result.domain or ""
            if any(auth in domain.lower() for auth in authoritative_domains):
                references.append(ExternalReference(
                    source_name=domain,
                    source_url=result.url,
                    source_type="article",
                    citation_context=result.snippet[:100],
                    suggested_placement=f"Reference when discussing {result.title[:50]}"
                ))
                
                if len(references) >= 4:
                    break
        
        # If we don't have enough from SERP, suggest general authoritative sources
        if len(references) < 2:
            prompt = f"""Suggest 3 authoritative external sources to cite in an article about "{serp_analysis.keyword}".

For each source, provide:
- Source name (publication/organization)
- Type (study, report, article, statistics)
- What information to cite
- Where in the article to place it

Return JSON array:
[
    {{
        "source_name": "Example Publication",
        "source_type": "study",
        "citation_context": "Key statistic or finding to cite",
        "suggested_placement": "In the section about X"
    }}
]"""

            try:
                refs_data = await llm_client.generate_json(
                    system_prompt="You are a research expert suggesting authoritative citations.",
                    user_prompt=prompt,
                    temperature=0.5
                )
                
                for ref in refs_data[:3] if isinstance(refs_data, list) else []:
                    references.append(ExternalReference(
                        source_name=ref.get("source_name", ""),
                        source_url="",  # URL to be researched
                        source_type=ref.get("source_type", "article"),
                        citation_context=ref.get("citation_context", ""),
                        suggested_placement=ref.get("suggested_placement", "")
                    ))
            except Exception as e:
                logger.error(f"Error generating external references: {str(e)}")
        
        return references[:4]
    
    def _analyze_keywords(
        self,
        article: GeneratedArticle,
        primary_keyword: str,
        secondary_keywords: List[str]
    ) -> KeywordAnalysis:
        """Analyze keyword usage in the article."""
        # Combine all text
        full_text = f"{article.title} {article.introduction} "
        for section in article.sections:
            full_text += f"{section.heading} {section.content} "
            for sub in section.subsections:
                full_text += f"{sub.heading} {sub.content} "
        full_text += article.conclusion
        
        full_text_lower = full_text.lower()
        primary_lower = primary_keyword.lower()
        
        # Count primary keyword
        primary_count = full_text_lower.count(primary_lower)
        total_words = len(full_text.split())
        density = (primary_count * len(primary_keyword.split()) / total_words * 100) if total_words > 0 else 0
        
        # Check keyword placement
        keyword_in_title = primary_lower in article.title.lower()
        keyword_in_intro = primary_lower in article.introduction.lower()[:500]
        
        # Count in headings
        headings_text = " ".join([s.heading.lower() for s in article.sections])
        keyword_in_headings = headings_text.count(primary_lower)
        
        # Count secondary keywords
        secondary_counts = {}
        for kw in secondary_keywords:
            count = full_text_lower.count(kw.lower())
            if count > 0:
                secondary_counts[kw] = count
        
        return KeywordAnalysis(
            primary_keyword=primary_keyword,
            primary_keyword_count=primary_count,
            primary_keyword_density=round(density, 2),
            secondary_keywords=secondary_counts,
            keyword_in_title=keyword_in_title,
            keyword_in_intro=keyword_in_intro,
            keyword_in_headings=keyword_in_headings
        )


# Singleton instance
article_generator = ArticleGenerator()
