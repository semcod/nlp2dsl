from nlp2cmd_intent import IntentPipeline


def test_file_search_intent_with_keyword_detector():
    pipeline = IntentPipeline()
    intent = pipeline.run("znajdź pliki *.py w src")
    assert intent.intent in {"file_search", "find"}
    assert intent.target_kind.value == "shell"
