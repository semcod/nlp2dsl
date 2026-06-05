"""Tests for nlp2cmd DetectionResult → IntentIR conversion."""

from dataclasses import dataclass, field

from nlp2cmd_intent import detection_to_intent_ir


@dataclass
class FakeDetection:
    domain: str
    intent: str
    confidence: float
    entities: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    matched: bool = True
    matched_keyword: str = ""


def test_detection_to_intent_ir_shell_find():
    result = FakeDetection(
        domain="shell",
        intent="find",
        confidence=0.95,
        entities={"pattern": "*.py", "path": "src"},
        matched_keyword="znajdź plik",
    )
    intent = detection_to_intent_ir(result, query="znajdź pliki *.py w src")
    assert intent.intent == "find"
    assert intent.target_kind.value == "shell"
    assert intent.entities.get("pattern") == "*.py"
    assert intent.execution_risk.value == "low"


def test_detection_to_intent_ir_browser_navigate():
    result = FakeDetection(
        domain="browser",
        intent="navigate",
        confidence=0.96,
        entities={"url": "https://jspaint.app"},
    )
    intent = detection_to_intent_ir(result, query="wejdź na jspaint.app")
    assert intent.target_kind.value == "browser"
    assert intent.entities.get("url") == "https://jspaint.app"
