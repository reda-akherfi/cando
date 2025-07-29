"""
Fuzzy search utilities for the Cando application.

This module provides fuzzy search functionality for finding projects and tasks
based on partial matches and relevance scoring.
"""

from difflib import SequenceMatcher
from typing import List, Tuple, Any
import re


def fuzzy_search(
    query: str, items: List[Any], search_fields: List[str], threshold: float = 0.3
) -> List[Tuple[Any, float]]:
    """
    Perform fuzzy search on a list of items.

    Args:
        query: The search query string
        items: List of items to search through
        search_fields: List of field names to search in (as strings)
        threshold: Minimum similarity score (0.0 to 1.0)

    Returns:
        List of tuples containing (item, relevance_score) sorted by relevance
    """
    if not query.strip():
        return [(item, 1.0) for item in items]

    query_lower = query.lower().strip()
    results = []

    for item in items:
        best_score = 0.0

        for field_name in search_fields:
            if hasattr(item, field_name):
                field_value = getattr(item, field_name)
                if field_value is None:
                    continue

                # Convert to string and search
                field_str = str(field_value).lower()

                # Check for exact substring match (highest priority)
                if query_lower in field_str:
                    score = 1.0
                # Check for word boundary matches
                elif any(word in field_str for word in query_lower.split()):
                    score = 0.8
                # Use fuzzy matching
                else:
                    score = SequenceMatcher(None, query_lower, field_str).ratio()

                best_score = max(best_score, score)

        # Also search in tags if the item has tags
        if hasattr(item, "tags") and item.tags:
            for tag in item.tags:
                tag_str = str(tag).lower()
                if query_lower in tag_str:
                    best_score = max(best_score, 0.9)
                elif any(word in tag_str for word in query_lower.split()):
                    best_score = max(best_score, 0.7)
                else:
                    tag_score = SequenceMatcher(None, query_lower, tag_str).ratio()
                    best_score = max(best_score, tag_score * 0.8)

        if best_score >= threshold:
            results.append((item, best_score))

    # Sort by relevance score (highest first)
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def highlight_search_terms(text: str, query: str) -> str:
    """
    Highlight search terms in text with HTML formatting.

    Args:
        text: The text to highlight
        query: The search query

    Returns:
        Text with highlighted search terms
    """
    if not query.strip():
        return text

    query_words = query.lower().split()
    text_lower = text.lower()
    highlighted_text = text

    for word in query_words:
        if word in text_lower:
            # Find the actual case in the original text
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            highlighted_text = pattern.sub(
                f'<span style="background-color: #ffeb3b; color: #000;">{word}</span>',
                highlighted_text,
            )

    return highlighted_text


def get_search_suggestions(
    query: str, items: List[Any], search_fields: List[str], max_suggestions: int = 5
) -> List[str]:
    """
    Get search suggestions based on partial matches.

    Args:
        query: The current search query
        items: List of items to generate suggestions from
        search_fields: List of field names to search in
        max_suggestions: Maximum number of suggestions to return

    Returns:
        List of suggestion strings
    """
    if not query.strip():
        return []

    query_lower = query.lower().strip()
    suggestions = set()

    for item in items:
        for field_name in search_fields:
            if hasattr(item, field_name):
                field_value = getattr(item, field_name)
                if field_value is None:
                    continue

                field_str = str(field_value)
                words = field_str.split()

                for word in words:
                    word_lower = word.lower()
                    if word_lower.startswith(query_lower) and len(word_lower) > len(
                        query_lower
                    ):
                        suggestions.add(word)

        # Also check tags
        if hasattr(item, "tags") and item.tags:
            for tag in item.tags:
                tag_str = str(tag)
                if tag_str.lower().startswith(query_lower):
                    suggestions.add(tag_str)

    return sorted(list(suggestions))[:max_suggestions]
