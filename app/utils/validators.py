"""SEO validation utilities."""
import re
from typing import List, Tuple, Dict, Any

from app.models.article import GeneratedArticle, ArticleSection, HeadingLevel


def validate_heading_hierarchy(article: GeneratedArticle) -> Tuple[bool, List[str]]:
    """Validate that heading hierarchy is correct (H1 > H2 > H3).
    
    Args:
        article: Article to validate
    
    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []
    
    # Title should be H1 (implicit)
    # All top-level sections should be H2
    for section in article.sections:
        if section.heading_level != HeadingLevel.H2:
            issues.append(f"Section '{section.heading}' should be H2, got {section.heading_level}")
        
        # All subsections should be H3
        for subsection in section.subsections:
            if subsection.heading_level != HeadingLevel.H3:
                issues.append(f"Subsection '{subsection.heading}' should be H3, got {subsection.heading_level}")
    
    return len(issues) == 0, issues


def validate_keyword_placement(
    article: GeneratedArticle,
    primary_keyword: str
) -> Tuple[bool, Dict[str, bool]]:
    """Validate keyword placement for SEO.
    
    Args:
        article: Article to validate
        primary_keyword: Primary keyword to check
    
    Returns:
        Tuple of (passes_basic_seo, placement_details)
    """
    keyword_lower = primary_keyword.lower()
    
    placements = {
        "in_title": keyword_lower in article.title.lower(),
        "in_meta_title": keyword_lower in article.seo_metadata.title_tag.lower(),
        "in_meta_description": keyword_lower in article.seo_metadata.meta_description.lower(),
        "in_introduction": keyword_lower in article.introduction.lower()[:500],
        "in_first_h2": (
            len(article.sections) > 0 and 
            keyword_lower in article.sections[0].heading.lower()
        ),
        "in_conclusion": keyword_lower in article.conclusion.lower()
    }
    
    # Must have at least title + intro + meta
    passes = (
        placements["in_title"] and 
        placements["in_introduction"] and
        (placements["in_meta_title"] or placements["in_meta_description"])
    )
    
    return passes, placements


def validate_word_count(
    article: GeneratedArticle,
    target: int,
    tolerance: float = 0.15
) -> Tuple[bool, Dict[str, Any]]:
    """Validate word count is within tolerance of target.
    
    Args:
        article: Article to validate
        target: Target word count
        tolerance: Acceptable deviation (default 15%)
    
    Returns:
        Tuple of (is_within_tolerance, details)
    """
    actual = article.total_word_count
    min_count = int(target * (1 - tolerance))
    max_count = int(target * (1 + tolerance))
    
    details = {
        "target": target,
        "actual": actual,
        "min_acceptable": min_count,
        "max_acceptable": max_count,
        "deviation_percent": round((actual - target) / target * 100, 1)
    }
    
    return min_count <= actual <= max_count, details


def validate_meta_lengths(article: GeneratedArticle) -> Tuple[bool, Dict[str, Any]]:
    """Validate SEO meta tag lengths.
    
    Args:
        article: Article to validate
    
    Returns:
        Tuple of (all_valid, details)
    """
    title_len = len(article.seo_metadata.title_tag)
    desc_len = len(article.seo_metadata.meta_description)
    
    details = {
        "title_tag_length": title_len,
        "title_tag_max": 60,
        "title_tag_valid": title_len <= 60,
        "meta_description_length": desc_len,
        "meta_description_max": 160,
        "meta_description_valid": desc_len <= 160
    }
    
    all_valid = details["title_tag_valid"] and details["meta_description_valid"]
    
    return all_valid, details


def validate_content_structure(article: GeneratedArticle) -> Tuple[bool, Dict[str, Any]]:
    """Validate overall content structure.
    
    Args:
        article: Article to validate
    
    Returns:
        Tuple of (is_well_structured, details)
    """
    num_sections = len(article.sections)
    num_subsections = sum(len(s.subsections) for s in article.sections)
    has_faq = len(article.faq_section) > 0
    has_internal_links = len(article.internal_links) >= 3
    has_external_refs = len(article.external_references) >= 2
    
    intro_words = len(article.introduction.split())
    conclusion_words = len(article.conclusion.split())
    
    details = {
        "num_h2_sections": num_sections,
        "num_h3_subsections": num_subsections,
        "has_sections": num_sections >= 3,
        "has_faq": has_faq,
        "faq_count": len(article.faq_section),
        "internal_links_count": len(article.internal_links),
        "has_enough_internal_links": has_internal_links,
        "external_refs_count": len(article.external_references),
        "has_enough_external_refs": has_external_refs,
        "introduction_words": intro_words,
        "conclusion_words": conclusion_words
    }
    
    is_well_structured = (
        details["has_sections"] and
        details["has_enough_internal_links"] and
        details["has_enough_external_refs"]
    )
    
    return is_well_structured, details


def run_all_validations(
    article: GeneratedArticle,
    target_word_count: int = 1500
) -> Dict[str, Any]:
    """Run all SEO validations on an article.
    
    Args:
        article: Article to validate
        target_word_count: Target word count
    
    Returns:
        Complete validation report
    """
    heading_valid, heading_issues = validate_heading_hierarchy(article)
    keyword_valid, keyword_placements = validate_keyword_placement(
        article, article.seo_metadata.primary_keyword
    )
    word_count_valid, word_count_details = validate_word_count(
        article, target_word_count
    )
    meta_valid, meta_details = validate_meta_lengths(article)
    structure_valid, structure_details = validate_content_structure(article)
    
    all_valid = all([
        heading_valid,
        keyword_valid,
        word_count_valid,
        meta_valid,
        structure_valid
    ])
    
    return {
        "overall_valid": all_valid,
        "validations": {
            "heading_hierarchy": {
                "valid": heading_valid,
                "issues": heading_issues
            },
            "keyword_placement": {
                "valid": keyword_valid,
                "placements": keyword_placements
            },
            "word_count": {
                "valid": word_count_valid,
                **word_count_details
            },
            "meta_tags": {
                "valid": meta_valid,
                **meta_details
            },
            "content_structure": {
                "valid": structure_valid,
                **structure_details
            }
        }
    }
