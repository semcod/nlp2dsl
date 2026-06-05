"""Keyword-based intent detection (canonical implementation)."""

from nlp2cmd_intent.data_files import find_data_files
from nlp2cmd_intent.keywords.keyword_detector import DetectionResult, KeywordIntentDetector
from nlp2cmd_intent.keywords.keyword_patterns import KeywordPatterns

__all__ = [
    "DetectionResult",
    "KeywordIntentDetector",
    "KeywordPatterns",
    "find_data_files",
]
