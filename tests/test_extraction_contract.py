from src.extraction.dual_path import VisionApiExtractor
from src.rotator.key_pool import KeyPool, ProviderKey

def test_api_extractor_uses_rotated_key_and_preserves_unknowns():
    observed = []
    def caller(family, key, png):
        observed.append((family, key, png))
        return {"markdown": "UNKNOWN", "latex": ["x^2"], "smiles": [], "questions": [], "confidence": 0.4}
    extraction = VisionApiExtractor(KeyPool([ProviderKey("gemini", 1, "secret")]), caller).extract_png(b"png")
    assert extraction.engine == "api:gemini_1"
    assert extraction.markdown == "UNKNOWN" and observed[0][2] == b"png"

def test_readable_page_text_does_not_poison_active_extraction_when_vision_fails():
    import httpx
    import pytest
    from src.rotator.key_pool import QuotaExhausted
    def unavailable(*args):
        import httpx
        request = httpx.Request("POST", "https://provider.invalid")
        raise httpx.HTTPStatusError("unavailable", request=request, response=httpx.Response(404, request=request))
    extractor = VisionApiExtractor(KeyPool([ProviderKey("gemini", 1, "secret")]), unavailable)
    with pytest.raises((QuotaExhausted, httpx.HTTPStatusError)):
        extractor.extract_png(b"png", text_clue="Q1. What is the SI unit of force?")
    # Verify text_fallback exists for diagnostic forensics but is disconnected from active extraction
    standalone = VisionApiExtractor.text_fallback("Q1. What is the SI unit of force?")
    assert standalone.engine == "text_fallback"
    assert standalone.questions[0]["stem"].startswith("Q1")

def test_json_payload_parsing_strips_code_fences_and_normalizes():
    from src.extraction.dual_path import _parse_json_payload
    wrapped = "```json\n{\"markdown\": \"# Force\", \"latex\": \"F=ma\", \"questions\": [{\"stem\": \"Q1\"}]}\n```"
    parsed = _parse_json_payload(wrapped)
    assert parsed["markdown"] == "# Force"
    assert parsed["latex"] == ["F=ma"]
    assert parsed["questions"] == [{"stem": "Q1"}]
    assert parsed["confidence"] == 0.85

def test_ollama_fallback_when_enabled(monkeypatch):
    import json
    import httpx
    monkeypatch.setenv("ENABLE_LOCAL_OLLAMA", "1")
    monkeypatch.setenv("OLLAMA_VISION_MODELS", "test-model")

    def mock_post(url, **kwargs):
        req = httpx.Request("POST", url)
        resp_data = {"message": {"content": json.dumps({"markdown": "Ollama page", "latex": [], "smiles": [], "questions": []})}}
        return httpx.Response(200, json=resp_data, request=req)

    monkeypatch.setattr(httpx, "post", mock_post)
    extractor = VisionApiExtractor(KeyPool([]))
    result = extractor.extract_png(b"png", text_clue="")
    assert result.engine == "local:ollama:test-model"
    assert result.markdown == "Ollama page"

