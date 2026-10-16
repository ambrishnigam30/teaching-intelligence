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
