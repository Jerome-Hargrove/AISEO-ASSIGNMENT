"""SERP (Search Engine Results Page) service for fetching and analyzing search results."""
import httpx
import logging
from typing import List, Optional
from datetime import datetime

from app.config import settings
from app.models.serp import SerpResult, SerpAnalysis, ExtractedTopic, ExtractedQuestion
from app.utils.llm_client import llm_client

logger = logging.getLogger(__name__)


class SerpService:
    """Service for fetching SERP data and analyzing competitive landscape."""
    
    def __init__(self):
        self.api_key = settings.serpapi_api_key
        self.base_url = "https://serpapi.com/search"
    
    async def fetch_serp_results(self, keyword: str, num_results: int = 10) -> List[SerpResult]:
        """Fetch top search results from SerpAPI.
        
        Args:
            keyword: Search keyword/topic
            num_results: Number of results to fetch (default 10)
        
        Returns:
            List of SerpResult objects
        """
        if not self.api_key:
            logger.warning("SerpAPI key not configured, using mock data")
            return self._get_mock_results(keyword)
        
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "q": keyword,
                    "api_key": self.api_key,
                    "engine": "google",
                    "num": num_results,
                    "gl": "us",
                    "hl": "en"
                }
                
                response = await client.get(self.base_url, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                results = []
                organic_results = data.get("organic_results", [])
                
                for i, item in enumerate(organic_results[:num_results], start=1):
                    result = SerpResult(
                        rank=i,
                        url=item.get("link", ""),
                        title=item.get("title", ""),
                        snippet=item.get("snippet", ""),
                        domain=item.get("displayed_link", "").split("/")[0] if item.get("displayed_link") else None
                    )
                    results.append(result)
                
                return results
                
        except httpx.HTTPError as e:
            logger.error(f"SerpAPI request failed: {str(e)}")
            logger.info("Falling back to mock data")
            return self._get_mock_results(keyword)
        except Exception as e:
            logger.error(f"Unexpected error fetching SERP data: {str(e)}")
            raise
    
    async def analyze_results(self, keyword: str, results: List[SerpResult]) -> SerpAnalysis:
        """Analyze SERP results to extract themes, topics, and keywords.
        
        Args:
            keyword: Original search keyword
            results: List of SERP results
        
        Returns:
            SerpAnalysis with extracted insights
        """
        # Prepare text for analysis
        results_text = "\n\n".join([
            f"Rank {r.rank}: {r.title}\nURL: {r.url}\nSnippet: {r.snippet}"
            for r in results
        ])
        
        analysis_prompt = f"""Analyze these top 10 search results for the keyword "{keyword}".

Extract and return JSON with:
1. "common_themes": List of 3-5 common themes across all results
2. "topics": List of objects with "topic", "frequency" (1-10), "importance" ("high"/"medium"/"low") - identify 5-8 main topics/subtopics covered
3. "primary_keywords": List of 3-5 primary keywords being targeted
4. "secondary_keywords": List of 5-10 related/secondary keywords
5. "questions": List of objects with "question" and "source" - extract 3-5 common questions users might have

Search Results:
{results_text}"""
        
        try:
            analysis_data = await llm_client.generate_json(
                system_prompt="You are an SEO analyst. Analyze search results and extract structured insights. Return only valid JSON.",
                user_prompt=analysis_prompt,
                temperature=0.3
            )
            
            # Parse topics
            topics = [
                ExtractedTopic(
                    topic=t.get("topic", ""),
                    frequency=t.get("frequency", 1),
                    importance=t.get("importance", "medium")
                )
                for t in analysis_data.get("topics", [])
            ]
            
            # Parse questions
            questions = [
                ExtractedQuestion(
                    question=q.get("question", q) if isinstance(q, dict) else q,
                    source=q.get("source", "serp") if isinstance(q, dict) else "serp"
                )
                for q in analysis_data.get("questions", [])
            ]
            
            return SerpAnalysis(
                keyword=keyword,
                total_results=len(results),
                results=results,
                common_themes=analysis_data.get("common_themes", []),
                topics=topics,
                primary_keywords=analysis_data.get("primary_keywords", []),
                secondary_keywords=analysis_data.get("secondary_keywords", []),
                questions=questions,
                analyzed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing SERP results: {str(e)}")
            # Return basic analysis without LLM insights
            return SerpAnalysis(
                keyword=keyword,
                total_results=len(results),
                results=results,
                common_themes=[],
                topics=[],
                primary_keywords=[keyword],
                secondary_keywords=[],
                questions=[],
                analyzed_at=datetime.utcnow()
            )
    
    async def get_full_analysis(self, keyword: str) -> SerpAnalysis:
        """Fetch SERP results and perform full analysis.
        
        Args:
            keyword: Search keyword/topic
        
        Returns:
            Complete SerpAnalysis
        """
        results = await self.fetch_serp_results(keyword)
        return await self.analyze_results(keyword, results)
    
    def _get_mock_results(self, keyword: str) -> List[SerpResult]:
        """Generate realistic mock SERP results for development/testing.
        
        Args:
            keyword: Search keyword (used to customize mock data)
        
        Returns:
            List of mock SerpResult objects
        """
        # Generate contextual mock data based on keyword
        keyword_lower = keyword.lower()
        
        if "productivity" in keyword_lower or "tools" in keyword_lower:
            return self._get_productivity_mock_results()
        elif "seo" in keyword_lower:
            return self._get_seo_mock_results()
        else:
            return self._get_generic_mock_results(keyword)
    
    def _get_productivity_mock_results(self) -> List[SerpResult]:
        """Mock results for productivity-related queries."""
        return [
            SerpResult(
                rank=1,
                url="https://www.forbes.com/advisor/business/best-productivity-tools/",
                title="15 Best Productivity Tools for Remote Teams in 2025",
                snippet="Discover the top productivity tools that help remote teams collaborate effectively. From project management to communication, these tools boost team efficiency.",
                domain="forbes.com"
            ),
            SerpResult(
                rank=2,
                url="https://www.pcmag.com/picks/the-best-productivity-apps",
                title="The Best Productivity Apps for 2025 | PCMag",
                snippet="We've tested dozens of productivity apps to find the best ones for managing tasks, time tracking, and improving focus. Here are our top picks.",
                domain="pcmag.com"
            ),
            SerpResult(
                rank=3,
                url="https://www.hubspot.com/productivity-tools",
                title="50+ Productivity Tools to Organize Your Work and Life",
                snippet="Looking for the best productivity tools? We've compiled a comprehensive list of apps for task management, note-taking, time tracking, and more.",
                domain="hubspot.com"
            ),
            SerpResult(
                rank=4,
                url="https://www.atlassian.com/blog/productivity/remote-team-tools",
                title="Essential Tools for Remote Team Productivity | Atlassian",
                snippet="Remote teams need the right tools to stay productive. Learn about the essential software for communication, collaboration, and project management.",
                domain="atlassian.com"
            ),
            SerpResult(
                rank=5,
                url="https://zapier.com/blog/best-productivity-apps/",
                title="The 25 Best Productivity Apps in 2025 | Zapier",
                snippet="These productivity apps will help you manage your time, tasks, and projects more effectively. Find the perfect tools for your workflow.",
                domain="zapier.com"
            ),
            SerpResult(
                rank=6,
                url="https://www.techradar.com/best/best-productivity-apps",
                title="Best Productivity Apps 2025: Top Tools for Getting Things Done",
                snippet="Our roundup of the best productivity apps includes options for task management, calendar organization, and focus enhancement.",
                domain="techradar.com"
            ),
            SerpResult(
                rank=7,
                url="https://www.businessnewsdaily.com/6498-productivity-tools.html",
                title="12 Best Team Productivity Tools for Small Businesses",
                snippet="Small businesses need efficient tools to maximize productivity. These are the best options for team collaboration and project management.",
                domain="businessnewsdaily.com"
            ),
            SerpResult(
                rank=8,
                url="https://monday.com/blog/productivity/productivity-tools/",
                title="Best Productivity Tools for Teams: A Complete Guide",
                snippet="Learn how to choose the right productivity tools for your team. Compare features, pricing, and use cases for popular options.",
                domain="monday.com"
            ),
            SerpResult(
                rank=9,
                url="https://www.notion.so/product/teams",
                title="Notion for Teams - All-in-One Productivity Platform",
                snippet="Notion combines notes, docs, wikis, and project management in one tool. Perfect for remote teams looking to centralize their work.",
                domain="notion.so"
            ),
            SerpResult(
                rank=10,
                url="https://www.g2.com/categories/productivity-tools",
                title="Best Productivity Software in 2025 | G2 Rankings",
                snippet="Compare the best productivity tools based on verified user reviews. See ratings, features, and pricing to find the right solution.",
                domain="g2.com"
            )
        ]
    
    def _get_seo_mock_results(self) -> List[SerpResult]:
        """Mock results for SEO-related queries."""
        return [
            SerpResult(
                rank=1,
                url="https://moz.com/beginners-guide-to-seo",
                title="The Beginner's Guide to SEO - Moz",
                snippet="Learn everything you need to know about search engine optimization with this comprehensive guide. From keywords to link building.",
                domain="moz.com"
            ),
            SerpResult(
                rank=2,
                url="https://ahrefs.com/blog/seo-basics/",
                title="SEO Basics: A Beginner's Guide to SEO | Ahrefs",
                snippet="Master the fundamentals of SEO with this step-by-step guide. Learn about on-page, off-page, and technical SEO strategies.",
                domain="ahrefs.com"
            ),
            SerpResult(
                rank=3,
                url="https://backlinko.com/seo-this-year",
                title="SEO in 2025: The Definitive Guide | Backlinko",
                snippet="The complete guide to ranking higher in Google this year. Updated strategies for modern SEO success.",
                domain="backlinko.com"
            ),
            SerpResult(
                rank=4,
                url="https://semrush.com/blog/seo-checklist/",
                title="The Ultimate SEO Checklist for 2025 | Semrush",
                snippet="Follow this comprehensive SEO checklist to optimize your website for search engines. Covers technical, on-page, and off-page factors.",
                domain="semrush.com"
            ),
            SerpResult(
                rank=5,
                url="https://neilpatel.com/what-is-seo/",
                title="What is SEO? Search Engine Optimization Explained",
                snippet="Understanding SEO is crucial for online success. Learn what SEO is and how it works in this detailed explanation.",
                domain="neilpatel.com"
            ),
            SerpResult(
                rank=6,
                url="https://searchengineland.com/guide/what-is-seo",
                title="What Is SEO / Search Engine Optimization?",
                snippet="SEO stands for search engine optimization. It's the practice of optimizing websites to rank higher in search results.",
                domain="searchengineland.com"
            ),
            SerpResult(
                rank=7,
                url="https://yoast.com/what-is-seo/",
                title="What is SEO? A Complete Guide | Yoast",
                snippet="SEO helps your website get found in search engines. Learn the basics and best practices in this comprehensive guide.",
                domain="yoast.com"
            ),
            SerpResult(
                rank=8,
                url="https://www.hubspot.com/marketing/seo",
                title="SEO Marketing: A Complete Guide | HubSpot",
                snippet="Learn how to use SEO to drive organic traffic to your website. Covers keyword research, content optimization, and more.",
                domain="hubspot.com"
            ),
            SerpResult(
                rank=9,
                url="https://developers.google.com/search/docs/fundamentals/seo-starter-guide",
                title="Google SEO Starter Guide",
                snippet="Google's official guide to SEO best practices. Learn how to make your site more visible in Google Search.",
                domain="developers.google.com"
            ),
            SerpResult(
                rank=10,
                url="https://www.searchenginejournal.com/seo-guide/",
                title="SEO 101: A Complete Guide to Search Engine Optimization",
                snippet="Everything you need to know about SEO in one comprehensive guide. Updated for the latest algorithm changes.",
                domain="searchenginejournal.com"
            )
        ]
    
    def _get_generic_mock_results(self, keyword: str) -> List[SerpResult]:
        """Generate generic mock results for any keyword."""
        base_domains = [
            "forbes.com", "wikipedia.org", "medium.com", "nytimes.com",
            "businessinsider.com", "techcrunch.com", "theverge.com",
            "entrepreneur.com", "inc.com", "fastcompany.com"
        ]
        
        results = []
        for i, domain in enumerate(base_domains, start=1):
            results.append(SerpResult(
                rank=i,
                url=f"https://www.{domain}/{keyword.replace(' ', '-').lower()}",
                title=f"{keyword.title()} - Complete Guide {2025} | {domain.split('.')[0].title()}",
                snippet=f"Learn everything about {keyword}. This comprehensive guide covers all aspects including best practices, tips, and expert advice.",
                domain=domain
            ))
        
        return results


# Singleton instance
serp_service = SerpService()
