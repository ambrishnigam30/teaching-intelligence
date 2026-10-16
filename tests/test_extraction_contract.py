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

def test_readable_page_text_is_a_deterministic_fallback_when_all_vision_calls_fail():
    def unavailable(*args):
        import httpx
        request = httpx.Request("POST", "https://provider.invalid")
        raise httpx.HTTPStatusError("unavailable", request=request, response=httpx.Response(404, request=request))
    extractor = VisionApiExtractor(KeyPool([ProviderKey("gemini", 1, "secret")]), unavailable)
    result = extractor.extract_png(b"png", text_clue="Q1. What is the SI unit of force?")
    assert result.engine == "text_fallback"
    assert result.questions[0]["stem"].startswith("Q1")
