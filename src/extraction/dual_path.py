from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import base64
import json
from pathlib import Path
from typing import Protocol
import re

import httpx
from src.rotator.key_pool import KeyPool, QuotaExhausted

VISION_PROMPT = """Transcribe this JEE/NEET teaching page faithfully. Return JSON with markdown, latex, smiles, questions, diagrams. Reconcile the supplied PDF text clue with the page image. Never invent unreadable content; use UNKNOWN for uncertain fields."""
GEMINI_VISION_MODELS = ("gemini-3.8-flash", "gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro")
GROQ_VISION_MODELS = ("meta-llama/llama-4-scout-17b-16e-instruct", "meta-llama/llama-4-maverick-17b-128e-instruct")
GROQ_TEXT_MODELS = ("llama-3.3-70b-versatile", "qwen/qwen3-32b")
OPENROUTER_VISION_MODELS = ("google/gemma-4-31b-it:free", "google/gemma-4-26b-a4b-it:free", "qwen/qwen3.8-27b:free", "thinkingmachines/inkling-small:free", "openrouter/free")

@dataclass(frozen=True)
class ExtractionResult:
    markdown: str
    latex: list[str]
    smiles: list[str]
    questions: list[dict]
    confidence: float
    engine: str

class VisionCaller(Protocol):
    def __call__(self, family: str, key: str, png: bytes, text_clue: str = "") -> dict: ...

class HttpVisionCaller:
    @staticmethod
    def _choose_dynamic_model(response: httpx.Response, family: str) -> str:
        payload = response.json().get("models", response.json().get("data", []))
        for model in payload:
            if family == "gemini":
                if "generateContent" in model.get("supportedGenerationMethods", []): return model["name"].removeprefix("models/")
            elif "image" in model.get("architecture", {}).get("input_modalities", []):
                return model["id"]
        raise RuntimeError(f"No active {family} image-capable model was returned by its Models API")

    def _gemini(self, key: str, parts: list[dict]) -> dict:
        headers = {"x-goog-api-key": key}
        base = "https://generativelanguage.googleapis.com/v1beta"
        payload = {"contents": [{"parts": parts}], "generationConfig": {"responseMimeType": "application/json"}}
        models = list(GEMINI_VISION_MODELS)
        for dynamic in (False, True):
            for model in models:
                response = httpx.post(f"{base}/models/{model}:generateContent", headers=headers, json=payload, timeout=90)
                if response.status_code == 404: continue
                response.raise_for_status()
                return json.loads(response.json()["candidates"][0]["content"]["parts"][0]["text"])
            if dynamic:
                break
            models = [self._choose_dynamic_model(httpx.get(f"{base}/models", headers=headers, timeout=30), "gemini")]
        response.raise_for_status()
        raise RuntimeError("Gemini model fallback exhausted")

    def _openai_compatible(self, endpoint: str, models_endpoint: str, key: str, models: tuple[str, ...], parts: list[dict], family: str) -> dict:
        headers = {"Authorization": "Bearer " + key}
        content = [{"type": "text", "text": VISION_PROMPT + "\n\nPDF text clue:\n" + parts[0]["text"]}, {"type": "image_url", "image_url": {"url": parts[1]["inline_data"]["data"]}}]
        payload = {"response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": content}]}
        candidates = list(models)
        for dynamic in (False, True):
            for model in candidates:
                response = httpx.post(endpoint, headers=headers, json={**payload, "model": model}, timeout=90)
                if response.status_code == 404: continue
                response.raise_for_status()
                return json.loads(response.json()["choices"][0]["message"]["content"])
            if dynamic: break
            listing = httpx.get(models_endpoint, headers=headers, timeout=30); listing.raise_for_status()
            candidates = [self._choose_dynamic_model(listing, family)]
        response.raise_for_status()
        raise RuntimeError(f"{family} model fallback exhausted")

    def __call__(self, family: str, key: str, png: bytes, text_clue: str = "") -> dict:
        image = base64.b64encode(png).decode("ascii")
        parts = [{"text": VISION_PROMPT + "\n\nPDF text clue:\n" + text_clue[:12000]}, {"inline_data": {"mime_type": "image/png", "data": image}}]
        if family == "gemini":
            return self._gemini(key, parts)
        encoded_parts = [parts[0], {"inline_data": {"data": "data:image/png;base64," + image}}]
        if family == "groq": return self._openai_compatible("https://api.groq.com/openai/v1/chat/completions", "https://api.groq.com/openai/v1/models", key, GROQ_VISION_MODELS, encoded_parts, "groq")
        return self._openai_compatible("https://openrouter.ai/api/v1/chat/completions", "https://openrouter.ai/api/v1/models", key, OPENROUTER_VISION_MODELS, encoded_parts, "openrouter")

class VisionApiExtractor:
    def __init__(self, pool: KeyPool, caller: VisionCaller | None = None):
        self.pool, self.caller = pool, caller or HttpVisionCaller()

    @staticmethod
    def render_pages(pdf: bytes, dpi: int = 300) -> list[bytes]:
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PyMuPDF is required for visual extraction; install the vision extra") from exc
        document = fitz.open(stream=pdf, filetype="pdf")
        try:
            scale = dpi / 72
            return [page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False).tobytes("png") for page in document]
        finally:
            document.close()

    @staticmethod
    def render_page(document_path: Path, page_number: int, dpi: int = 300) -> tuple[bytes, list[bytes], str]:
        """Render one PDF page and extract embedded raster diagrams as independent PNG crops."""
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PyMuPDF is required for visual extraction; install the vision extra") from exc
        document = fitz.open(document_path)
        try:
            page = document[page_number]
            pixmap = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
            diagrams = []
            for image in page.get_images(full=True):
                extracted = document.extract_image(image[0])
                if extracted.get("width", 0) >= 64 and extracted.get("height", 0) >= 64:
                    diagrams.append(extracted["image"])
            return pixmap.tobytes("png"), diagrams, page.get_text("text")
        finally:
            document.close()

    def extract_png(self, png: bytes, author_family: str | None = None, text_clue: str = "") -> ExtractionResult:
        last_error: Exception | None = None
        # Exhaust the interleaved 15-key pool before deferring a rate-limited visual page.
        for _ in range(len(self.pool.keys)):
            key = self.pool.acquire(exclude_family=author_family)
            try:
                try:
                    data = self.caller(key.family, key.value, png, text_clue)
                except TypeError:  # Supports pre-existing three-argument test callers.
                    data = self.caller(key.family, key.value, png)
                return ExtractionResult(markdown=data.get("markdown", "UNKNOWN"), latex=data.get("latex", []), smiles=data.get("smiles", []), questions=data.get("questions", []), confidence=float(data.get("confidence", 0)), engine=f"api:{key.label}")
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code in {400, 401, 403, 404, 429, 500, 503}: self.pool.cooldown(key, seconds=300)
            except (httpx.TransportError, json.JSONDecodeError, KeyError, RuntimeError) as exc:
                last_error = exc; self.pool.cooldown(key, seconds=120)
        if text_clue.strip(): return self.text_fallback(text_clue)
        if last_error: raise last_error
        raise QuotaExhausted("No provider key is available for visual extraction")

    @staticmethod
    def text_fallback(text: str) -> ExtractionResult:
        readable = " ".join(text.split())
        latex = re.findall(r"\$([^$]+)\$|\\\(([^)]+)\\\)", text)
        expressions = [a or b for a, b in latex]
        questions = [{"stem": line.strip()} for line in text.splitlines() if re.match(r"^\s*(?:Q(?:uestion)?\s*)?\d+[.)]", line, re.I)]
        return ExtractionResult(markdown=readable or "UNKNOWN", latex=expressions, smiles=[], questions=questions, confidence=0.55, engine="text_fallback")

class KaggleBatchDispatcher(Protocol):
    def dispatch(self, input_manifest: dict) -> str: ...

class DualPathExtractor:
    """Cloud API path always runs; private Kaggle accelerates queued heavy OCR when configured."""
    def __init__(self, api: VisionApiExtractor, kaggle: KaggleBatchDispatcher | None = None):
        self.api, self.kaggle = api, kaggle

    def extract_pdf(self, pdf: bytes, source_id: str, heavy: bool = False) -> list[ExtractionResult]:
        results = [self.api.extract_png(page) for page in self.api.render_pages(pdf, dpi=300)]
        if heavy and self.kaggle:
            self.kaggle.dispatch({"source_id": source_id, "pages": len(results), "private": True})
        return results
