"""Quality scorer for evaluating and improving generated content."""
import logging
from typing import Dict, Any, List, Tuple

from app.models.article import GeneratedArticle, KeywordAnalysis
from app.utils.llm_client import llm_client

logger = logging.getLogger(__name__)


class QualityScorer:
    """Evaluate article quality and SEO compliance."""
    
    # Minimum thresholds for quality
    MIN_KEYWORD_DENSITY = 0.5
    MAX_KEYWORD_DENSITY = 3.0
    MIN_WORD_COUNT_RATIO = 0.8  # At least 80% of target
    MAX_WORD_COUNT_RATIO = 1.2  # At most 120% of target
    
    def evaluate_article(
        self,
        article: GeneratedArticle,
        target_word_count: int = 1500
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Evaluate article quality and return score with issues.
        
        Args:
            article: Generated article to evaluate
            target_word_count: Target word count
        
        Returns:
            Tuple of (score 0-100, list of issues)
        """
        issues = []
        score = 100.0
        
        # Check keyword placement
        if not article.keyword_analysis.keyword_in_title:
            issues.append({
                "type": "seo",
                "severity": "high",
                "message": "Primary keyword not in title",
                "suggestion": "Add primary keyword to the article title"
            })
            score -= 15
        
        if not article.keyword_analysis.keyword_in_intro:
            issues.append({
                "type": "seo",
                "severity": "high",
                "message": "Primary keyword not in introduction",
                "suggestion": "Include primary keyword in the first paragraph"
            })
            score -= 15
        
        # Check keyword density
        density = article.keyword_analysis.primary_keyword_density
        if density < self.MIN_KEYWORD_DENSITY:
            issues.append({
                "type": "seo",
                "severity": "medium",
                "message": f"Keyword density too low ({density:.1f}%)",
                "suggestion": f"Increase keyword usage (target: {self.MIN_KEYWORD_DENSITY}-{self.MAX_KEYWORD_DENSITY}%)"
            })
            score -= 10
        elif density > self.MAX_KEYWORD_DENSITY:
            issues.append({
                "type": "seo",
                "severity": "medium",
                "message": f"Keyword density too high ({density:.1f}%)",
                "suggestion": "Reduce keyword stuffing for natural reading"
            })
            score -= 10
        
        # Check word count
        word_count = article.total_word_count
        min_words = int(target_word_count * self.MIN_WORD_COUNT_RATIO)
        max_words = int(target_word_count * self.MAX_WORD_COUNT_RATIO)
        
        if word_count < min_words:
            issues.append({
                "type": "content",
                "severity": "high",
                "message": f"Article too short ({word_count} words, target: {target_word_count})",
                "suggestion": "Expand sections with more detail"
            })
            score -= 15
        elif word_count > max_words:
            issues.append({
                "type": "content",
                "severity": "low",
                "message": f"Article longer than target ({word_count} words, target: {target_word_count})",
                "suggestion": "Consider trimming content for conciseness"
            })
            score -= 5
        
        # Check heading structure
        heading_issues = self._check_heading_structure(article)
        for issue in heading_issues:
            issues.append(issue)
            score -= 5
        
        # Check internal links
        if len(article.internal_links) < 3:
            issues.append({
                "type": "seo",
                "severity": "low",
                "message": f"Insufficient internal links ({len(article.internal_links)})",
                "suggestion": "Add 3-5 internal linking opportunities"
            })
            score -= 5
        
        # Check external references
        if len(article.external_references) < 2:
            issues.append({
                "type": "seo",
                "severity": "low",
                "message": f"Insufficient external references ({len(article.external_references)})",
                "suggestion": "Add 2-4 authoritative external citations"
            })
            score -= 5
        
        # Check FAQ section
        if len(article.faq_section) == 0:
            issues.append({
                "type": "content",
                "severity": "low",
                "message": "No FAQ section",
                "suggestion": "Add FAQ section for featured snippets opportunity"
            })
            score -= 5
        
        # Ensure score is within bounds
        score = max(0, min(100, score))
        
        return score, issues
    
    def _check_heading_structure(self, article: GeneratedArticle) -> List[Dict[str, Any]]:
        """Check heading hierarchy for SEO compliance."""
        issues = []
        
        # Check if there are any sections
        if not article.sections:
            issues.append({
                "type": "structure",
                "severity": "high",
                "message": "No H2 sections in article",
                "suggestion": "Add structured sections with H2 headings"
            })
            return issues
        
        # Check for H2 sections
        h2_count = len(article.sections)
        if h2_count < 3:
            issues.append({
                "type": "structure",
                "severity": "medium",
                "message": f"Too few H2 sections ({h2_count})",
                "suggestion": "Add more main sections (recommended: 4-6)"
            })
        
        return issues
    
    async def suggest_improvements(
        self,
        article: GeneratedArticle,
        issues: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate specific improvement suggestions using LLM.
        
        Args:
            article: The article to improve
            issues: List of identified issues
        
        Returns:
            List of specific improvement suggestions
        """
        if not issues:
            return ["Article meets all quality criteria!"]
        
        issues_text = "\n".join([
            f"- {issue['type'].upper()}: {issue['message']} (Suggestion: {issue['suggestion']})"
            for issue in issues
        ])
        
        prompt = f"""An article about "{article.seo_metadata.primary_keyword}" has the following issues:

{issues_text}

Current article title: {article.title}
Current word count: {article.total_word_count}

Provide 3-5 specific, actionable improvements to fix these issues. Be concrete and provide examples where possible.

Return JSON:
{{
    "improvements": [
        "Specific improvement suggestion 1",
        "Specific improvement suggestion 2"
    ]
}}"""

        try:
            result = await llm_client.generate_json(
                system_prompt="You are an SEO and content quality expert providing actionable improvements.",
                user_prompt=prompt,
                temperature=0.5
            )
            return result.get("improvements", [])
        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {str(e)}")
            return [issue["suggestion"] for issue in issues]
    
    def passes_quality_check(
        self,
        article: GeneratedArticle,
        target_word_count: int = 1500,
        min_score: float = 70.0
    ) -> Tuple[bool, float, List[Dict[str, Any]]]:
        """Check if article passes minimum quality threshold.
        
        Args:
            article: Article to evaluate
            target_word_count: Target word count
            min_score: Minimum acceptable score
        
        Returns:
            Tuple of (passes, score, issues)
        """
        score, issues = self.evaluate_article(article, target_word_count)
        passes = score >= min_score
        
        if not passes:
            logger.warning(f"Article failed quality check: {score:.1f} < {min_score}")
        
        return passes, score, issues


# Singleton instance
quality_scorer = QualityScorer()
