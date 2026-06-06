"""
Keyword-based intent detection logic.

This module contains the core detection algorithms and logic
for matching keywords to intents and domains.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Optional

from .keyword_patterns import KeywordPatterns

logger = logging.getLogger(__name__)

# Lazy imports for heavy dependencies
_polish_support = None
_fuzzy_schema_matcher = None
_ml_classifier = None
_semantic_matcher = None
_spacy = None
_nlp_model = None
_nlp_model_loaded = False
_query_normalizer = None


def _get_query_normalizer():
    """Lazy load QueryNormalizer."""
    global _query_normalizer
    if _query_normalizer is None:
        try:
            from nlp2cmd.nlp.normalizer import QueryNormalizer
            _query_normalizer = QueryNormalizer()
        except ImportError:
            try:
                from nlp2cmd_intent.normalize import QueryNormalizer
                _query_normalizer = QueryNormalizer()
            except ImportError:
                _query_normalizer = False
    return _query_normalizer if _query_normalizer else None


def _get_polish_support():
    """Lazy load Polish support to avoid circular imports."""
    global _polish_support
    if _polish_support is None:
        try:
            from nlp2cmd.polish_support import polish_support
            _polish_support = polish_support
        except ImportError:
            _polish_support = False
    return _polish_support if _polish_support else None


def _get_fuzzy_schema_matcher():
    """Lazy load FuzzySchemaMatcher with multilingual phrases."""
    global _fuzzy_schema_matcher
    if _fuzzy_schema_matcher is None:
        try:
            from nlp2cmd.generation.fuzzy_schema_matcher import FuzzySchemaMatcher
            from pathlib import Path
            
            schema_paths = [
                Path(__file__).parent.parent.parent.parent / "data" / "multilingual_phrases.json",
                Path("data/multilingual_phrases.json"),
                Path("multilingual_phrases.json"),
            ]
            
            matcher = FuzzySchemaMatcher()
            for path in schema_paths:
                if path.exists():
                    matcher.load_schema(path)
                    break
            
            if not matcher.phrases:
                from nlp2cmd.generation.fuzzy_schema_matcher import create_multilingual_matcher
                matcher = create_multilingual_matcher()
            
            _fuzzy_schema_matcher = matcher
        except ImportError:
            _fuzzy_schema_matcher = False
    return _fuzzy_schema_matcher if _fuzzy_schema_matcher else None


def _get_ml_classifier():
    """Lazy load ML intent classifier for high-accuracy predictions."""
    global _ml_classifier
    enable_ml = str(
        os.environ.get("NLP2CMD_ENABLE_ML_CLASSIFIER")
        or os.environ.get("NLP2CMD_ENABLE_HEAVY_NLP")
        or ""
    ).strip().lower() in {"1", "true", "yes", "y", "on"}
    
    if not enable_ml:
        return None
    
    if _ml_classifier is None:
        try:
            from nlp2cmd.generation.ml_intent_classifier import get_ml_classifier
            _ml_classifier = get_ml_classifier()
            if _ml_classifier is None:
                _ml_classifier = False
        except ImportError:
            _ml_classifier = False
    return _ml_classifier if _ml_classifier else None


def _get_semantic_matcher():
    """Lazy load semantic matcher for high-accuracy predictions."""
    global _semantic_matcher
    enable_semantic = str(
        os.environ.get("NLP2CMD_ENABLE_SEMANTIC_MATCHING")
        or os.environ.get("NLP2CMD_ENABLE_HEAVY_NLP")
        or ""
    ).strip().lower() in {"1", "true", "yes", "y", "on"}
    
    if not enable_semantic:
        return None
    
    if _semantic_matcher is None:
        try:
            from nlp2cmd.generation.semantic_matcher_optimized import OptimizedSemanticMatcher
            _semantic_matcher = OptimizedSemanticMatcher()
        except ImportError:
            _semantic_matcher = False
    return _semantic_matcher if _semantic_matcher else None


def _get_spacy_model():
    """Lazy load spaCy model for lemmatization."""
    global _spacy, _nlp_model, _nlp_model_loaded
    enable_spacy = str(
        os.environ.get("NLP2CMD_ENABLE_SPACY_LEMMATIZATION")
        or os.environ.get("NLP2CMD_ENABLE_HEAVY_NLP")
        or ""
    ).strip().lower() in {"1", "true", "yes", "y", "on"}
    
    if not enable_spacy:
        return None
    
    if _nlp_model_loaded:
        return _nlp_model
    
    try:
        import spacy
        _spacy = spacy
        
        # Try to load Polish model first, fall back to English
        try:
            _nlp_model = spacy.load("pl_core_news_sm")
        except OSError:
            try:
                _nlp_model = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("No spaCy model available, falling back to basic tokenization")
                _nlp_model = None
        
        _nlp_model_loaded = True
        return _nlp_model
        
    except ImportError:
        logger.debug("spaCy not available")
        _nlp_model_loaded = True
        return None


def _normalize_url(raw: str) -> str:
    """Normalize URL by adding https:// if needed."""
    u = (raw or "").strip().strip('""')
    if not u:
        return u
    if u.startswith("http://") or u.startswith("https://") or u.startswith("file://"):
        return u
    if u.startswith("www."):
        return f"https://{u}"
    # If it looks like a domain[/path], default to https
    # Regex: starts with alphanumeric, then alphanumeric/hyphen/dot, then a dot, then 2+ letters,
    # optionally followed by a path (non-whitespace/quote chars)
    if re.match(r"^[a-zA-Z0-9][\w\-\.]*\.[a-zA-Z]{2,}(?:/[^\s'\"]*)?$", u):
        return f"https://{u}"
    return u


@dataclass
class DetectionResult:
    """Result of intent detection."""
    
    domain: str
    intent: str
    confidence: float
    entities: dict[str, str] = None
    metadata: dict[str, any] = None
    matched: bool = True  # Whether detection was successful
    matched_keyword: str = ""  # The keyword that triggered this detection
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = {}
        if self.metadata is None:
            self.metadata = {}


_BROWSER_OVERRIDE_PATTERNS = (
    r"otw[oó]rz\s+przegl[aą]dark[eę]",
    r"uruchom\s+przegl[aą]dark[eę]",
    r"w[łl][aą]cz\s+przegl[aą]dark[eę]",
    r"(?:wejd[zź]|przejd[zź]|id[zź])\s+na\s+stron[eę]",
    r"otw[oó]rz\s+stron[eę]",
    r"(?:otw[oó]rz|wejd[zź]|uruchom).+\.[a-z]{2,}",
)

_BROWSER_ANTI_NETWORKING_SIGNALS = (
    "przegladark", "przeglądark", "stron", "tab", "kart",
    ".com", ".org", ".net", ".io", ".ai", ".pl", ".app",
    "klucz", "api", "key", "token", "formularz",
)


def _super_fast_browser_override(text_lower: str) -> Optional[DetectionResult]:
    try:
        if not any(re.search(p, text_lower) for p in _BROWSER_OVERRIDE_PATTERNS):
            return None
        url_match = re.search(r"\b(https?://[^\s'\"]+)", text_lower)
        domain_in_text = re.search(
            r"\b([a-zA-Z0-9][\w\-]*\.(?:com|org|net|io|ai|dev|pl|app|co|de|uk|eu)(?:/[^\s'\"]*)?)",
            text_lower,
        )
        entities: dict[str, str] = {}
        if url_match:
            entities["url"] = _normalize_url(url_match.group(1))
        elif domain_in_text:
            entities["url"] = _normalize_url(domain_in_text.group(1))
        return DetectionResult(
            domain="browser",
            intent="navigate",
            confidence=0.96,
            entities=entities,
            matched_keyword="super_fast_browser_override",
        )
    except Exception:
        return None


class KeywordIntentDetector:
    """
    Rule-based intent detection using keyword matching.
    
    No LLM needed - uses predefined keyword patterns to detect
    domain (sql, shell, docker, kubernetes) and intent.
    
    Example:
        detector = KeywordIntentDetector()
        result = detector.detect("Pokaż wszystkich użytkowników z tabeli users")
        # result.domain == 'sql', result.intent == 'select'
    """
    
    def __init__(
        self,
        patterns: Optional[KeywordPatterns] = None,
        confidence_threshold: float = 0.5,
        custom_patterns: Optional[dict] = None,
    ):
        """
        Initialize keyword detector.
        
        Args:
            patterns: KeywordPatterns instance or None to create default
            confidence_threshold: Minimum confidence to return a match
            custom_patterns: Optional dict of {domain: {intent: [patterns]}} to add
        """
        self.patterns = patterns or KeywordPatterns()
        self.confidence_threshold = confidence_threshold
        if custom_patterns:
            for domain, intents in custom_patterns.items():
                for intent, pats in intents.items():
                    self.patterns.add_pattern(domain, intent, pats)

    def add_pattern(self, domain: str, intent: str, patterns: list) -> None:
        """Add custom patterns for a domain/intent pair."""
        self.patterns.add_pattern(domain, intent, patterns)
    
    def _prepare_detect_text(self, text: str) -> tuple[str, str] | None:
        if not text or not text.strip():
            return None
        normalizer = _get_query_normalizer()
        if normalizer is not None:
            normalized = normalizer.normalize(text)
            text = normalized if isinstance(normalized, str) else normalized.text
        return text, text.lower()

    def _accept_detection(self, result: Optional[DetectionResult]) -> Optional[DetectionResult]:
        if result and result.confidence >= self.confidence_threshold:
            return result
        return None

    def detect(self, text: str) -> DetectionResult:
        """
        Detect domain and intent from text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            DetectionResult with detected domain, intent, and confidence
        """
        prepared = self._prepare_detect_text(text)
        if prepared is None:
            return DetectionResult(domain="unknown", intent="unknown", confidence=0.0, matched=False)
        text, text_lower = prepared

        if browser := _super_fast_browser_override(text_lower):
            return browser

        for candidate in (
            self._ml_detection(text),
            self._fuzzy_detection(text),
        ):
            if accepted := self._accept_detection(candidate):
                return accepted

        if fast_result := self._fast_path_detection(text_lower, domain_rules=bool(self.patterns.patterns)):
            return fast_result

        if accepted := self._accept_detection(self._semantic_detection(text)):
            return accepted

        result = self._keyword_detection(text, text_lower)
        result.matched = result.confidence >= self.confidence_threshold
        return result

    def detect_intent_ir(self, text: str):
        """Return pact-ir IntentIR for this detection."""
        from nlp2cmd_intent.nlp2cmd_convert import detection_to_intent_ir

        return detection_to_intent_ir(self.detect(text), query=text)

    def detect_all(self, text: str) -> list[DetectionResult]:
        """
        Detect all matching domains and intents.
        
        Args:
            text: Natural language input
            
        Returns:
            List of DetectionResult, sorted by confidence descending
        """
        if not text or not text.strip():
            return []
        
        text_lower = text.lower()
        results: list[DetectionResult] = []
        seen: set[tuple[str, str]] = set()
        
        # Get all possible matches from patterns
        for domain, intents in self.patterns.patterns.items():
            for intent, keywords in intents.items():
                for kw in keywords:
                    if self._match_keyword(text_lower, kw):
                        key = (domain, intent)
                        if key not in seen:
                            seen.add(key)
                            confidence = 0.7  # Base confidence for keyword matches
                            results.append(DetectionResult(
                                domain=domain,
                                intent=intent,
                                confidence=confidence
                            ))
        
        # Sort by confidence descending
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results
    
    def _match_keyword(self, text_lower: str, keyword: str) -> bool:
        """Simple keyword matching."""
        return keyword.lower() in text_lower
    
    def _fast_path_detection(self, text_lower: str, domain_rules: bool = True) -> Optional[DetectionResult]:
        """Fast path detection for common patterns."""
        from .fast_path_detection import fast_path_detect

        hit = fast_path_detect(text_lower, self.patterns, domain_rules=domain_rules)
        if hit is None:
            return None
        return DetectionResult(
            domain=hit.domain,
            intent=hit.intent,
            confidence=hit.confidence,
            entities=dict(hit.entities),
            matched_keyword=hit.matched_keyword,
        )

    def _fuzzy_detection(self, text: str) -> Optional[DetectionResult]:
        """Detection using fuzzy schema matching."""
        matcher = _get_fuzzy_schema_matcher()
        if not matcher:
            return None
        
        try:
            result = matcher.match(text)
            if result and result.confidence >= self.confidence_threshold:
                return DetectionResult(
                    domain=result.domain,
                    intent=result.intent,
                    confidence=result.confidence,
                    entities=result.entities or {},
                )
        except Exception as e:
            logger.debug(f"Fuzzy matching failed: {e}")
        
        return None
    
    def _ml_detection(self, text: str) -> Optional[DetectionResult]:
        """ML-based detection using trained classifier."""
        classifier = _get_ml_classifier()
        if not classifier:
            return None
        
        try:
            result = classifier.predict(text)
            if result and result.confidence >= self.confidence_threshold:
                return DetectionResult(
                    domain=result.domain,
                    intent=result.intent,
                    confidence=result.confidence,
                    entities=result.entities or {},
                )
        except Exception as e:
            logger.debug(f"ML detection failed: {e}")
        
        return None
    
    def _semantic_detection(self, text: str) -> Optional[DetectionResult]:
        """Semantic detection using sentence embeddings."""
        matcher = _get_semantic_matcher()
        if not matcher:
            return None
        
        try:
            result = matcher.match(text)
            if result and result.confidence >= self.confidence_threshold:
                return DetectionResult(
                    domain=result.domain,
                    intent=result.intent,
                    confidence=result.confidence,
                    entities=result.entities or {},
                )
        except Exception as e:
            logger.debug(f"Semantic matching failed: {e}")
        
        return None
    
    def _best_keyword_match(self, text_lower: str, *, priority_only: bool) -> DetectionResult:
        best = DetectionResult(domain="unknown", intent="unknown", confidence=0.0, matched=False)
        for domain in self.patterns.list_domains():
            intents = (
                self.patterns.get_priority_intents(domain)
                if priority_only
                else [
                    intent
                    for intent in self.patterns.list_intents(domain)
                    if intent not in self.patterns.get_priority_intents(domain)
                ]
            )
            for intent in intents:
                confidence = self._calculate_keyword_confidence(
                    text_lower,
                    self.patterns.get_intent_patterns(domain, intent),
                )
                if confidence > best.confidence:
                    best = DetectionResult(domain=domain, intent=intent, confidence=confidence)
        return best

    def _apply_domain_booster(self, match: DetectionResult, text_lower: str) -> DetectionResult:
        if not match.domain:
            return match
        boosters = self.patterns.get_domain_boosters(match.domain)
        if self._calculate_keyword_confidence(text_lower, boosters) > 0:
            match.confidence = min(1.0, match.confidence + 0.1)
        return match

    def _anti_networking_browser_override(
        self,
        match: DetectionResult,
        text_lower: str,
    ) -> DetectionResult:
        if match.domain != "networking_ext":
            return match
        if not any(signal in text_lower for signal in _BROWSER_ANTI_NETWORKING_SIGNALS):
            return match
        domain_match = re.search(
            r'\b([a-zA-Z0-9][\w\-]*\.(?:com|org|net|io|ai|dev|pl|app|co)(?:/[^\s\'\"]*)?)',
            text_lower,
        )
        entities = {"url": _normalize_url(domain_match.group(1))} if domain_match else {}
        return DetectionResult(
            domain="browser",
            intent="navigate",
            confidence=0.85,
            entities=entities,
            matched_keyword="anti_networking_override",
        )

    def _keyword_detection(self, text: str, text_lower: str) -> DetectionResult:
        """Traditional keyword-based detection."""
        best_match = self._best_keyword_match(text_lower, priority_only=True)
        if best_match.confidence < self.confidence_threshold:
            fallback = self._best_keyword_match(text_lower, priority_only=False)
            if fallback.confidence > best_match.confidence:
                best_match = fallback
        best_match = self._apply_domain_booster(best_match, text_lower)
        return self._anti_networking_browser_override(best_match, text_lower)
    
    def _calculate_keyword_confidence(self, text: str, keywords: list[str]) -> float:
        """Calculate confidence based on keyword matches."""
        if not keywords:
            return 0.0
        
        matches = 0
        total_keywords = len(keywords)
        
        # Use enhanced tokenization if available
        tokens = self._tokenize_text(text)
        token_set = set(tokens)
        
        for keyword in keywords:
            if self._keyword_matches(keyword, text, token_set):
                matches += 1
        
        if matches == 0:
            return 0.0
        
        # Base confidence from keyword matches
        base_confidence = matches / total_keywords
        
        # Boost for multiple matches
        if matches >= 2:
            base_confidence = min(1.0, base_confidence + 0.2)
        
        return base_confidence
    
    def _tokenize_text(self, text: str) -> list[str]:
        """Tokenize text using available tools."""
        # Try spaCy first
        nlp = _get_spacy_model()
        if nlp:
            try:
                doc = nlp(text)
                tokens = []
                polish_support = _get_polish_support()
                
                for token in doc:
                    if polish_support and hasattr(polish_support, '_is_important_token'):
                        if polish_support._is_important_token(token):
                            original_text = token.text.lower()
                            lemma = (token.lemma_ or "").lower()
                            important_keywords = {
                                'restartuj', 'uruchom', 'zrestartuj', 'startuj', 'wystartuj',
                                'zatrzymaj', 'stopuj', 'usuń', 'skopiuj', 'przenieś', 'znajdź',
                                'pokaż', 'sprawdź', 'utwórz', 'zmień', 'restart', 'docker', 'ps',
                                'kill', 'run', 'stop', 'start', 'create', 'delete', 'remove',
                                'katalog', 'katalogi', 'usługa', 'usługi', 'usługę', 'serwis',
                                'komputer', 'system', 'proces', 'procesy'
                            }
                            if original_text in important_keywords or not lemma or len(lemma) <= 1:
                                tokens.append(original_text)
                            else:
                                tokens.append(lemma)
                    else:
                        tokens.append(token.text.lower())
                return tokens
            except Exception as e:
                logger.debug(f"spaCy tokenization failed: {e}")
        
        # Fallback to basic tokenization
        return re.findall(r'\b\w+\b', text.lower())
    
    def _keyword_matches(self, keyword: str, text: str, tokens: set[str]) -> bool:
        """Check if a keyword matches the text."""
        # Direct token match
        if keyword in tokens:
            return True
        
        # Multi-word keyword matching
        if ' ' in keyword:
            pattern = r'\s+'.join(map(re.escape, keyword.split()))
            return re.search(pattern, text) is not None
        
        # Special patterns for single keywords
        if len(keyword) <= 3 and re.fullmatch(r"[a-z0-9]+", keyword):
            return re.search(rf"(?<![a-z0-9_]){re.escape(keyword)}(?![a-z0-9_])", text) is not None

        # For plain single-word keywords, avoid substring matches (e.g. "openrouter" contains "route").
        # Require word boundaries unless the keyword contains non-word chars.
        if re.fullmatch(r"[\w\-]+", keyword):
            return re.search(rf"(?<![\w]){re.escape(keyword)}(?![\w])", text) is not None

        # Fallback: substring search for non-word keywords (rare)
        return keyword in text
