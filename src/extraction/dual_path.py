from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import base64
import json
from pathlib import Path
from typing import Protocol

import httpx
from src.rotator.key_pool import KeyPool, QuotaExhausted

VISION_PROMPT = """Transcribe this JEE/NEET teaching page faithfully. Return JSON with markdown, latex, smiles, questions, diagrams. Never invent unreadable content; use UNKNOWN for uncertain fields."""

@dataclass(frozen=True)
class ExtractionResult:
    markdown: str
    latex: list[str]
    smiles: list[str]
    questions: list[dict]
    confidence: float
    engine: str

class VisionCaller(Protocol):
    def __call__(self, family: str, key: str, png: bytes) -> dict: ...

class HttpVisionCaller:
    def __call__(self, family: str, key: str, png: bytes) -> dict:
        image = base64.b64encode(png).decode("ascii")
        if family == "gemini":
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
            payload = {"contents": [{"parts": [{"text": VISION_PROMPT}, {"inline_data": {"mime_type": "image/png", "data": image}}]}], "generationConfig": {"responseMimeType": "application/json"}}
            response = httpx.post(url, params={"key": key}, json=payload, timeout=90)
            response.raise_for_status()
            text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:
            endpoint = "https://api.groq.com/openai/v1/chat/completions" if family == "groq" else "https://openrouter.ai/api/v1/chat/completions"
            model = "meta-llama/llama-4-scout-17b-16e-instruct" if family == "groq" else "google/gemini-2.5-flash"
            payload = {"model": model, "response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": [{"type": "text", "text": VISION_PROMPT}, {"type": "image_url", "image_url": {"url": "data:image/png;base64," + image}}]}]}
            response = httpx.post(endpoint, headers={"Authorization": "Bearer " + key}, json=payload, timeout=90)
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"]
        return json.loads(text)

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
    def render_page(document_path: Path, page_number: int, dpi: int = 300) -> tuple[bytes, list[bytes]]:
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
            return pixmap.tobytes("png"), diagrams
        finally:
            document.close()

    def extract_png(self, png: bytes, author_family: str | None = None) -> ExtractionResult:
        key = self.pool.acquire(exclude_family=author_family)
        try:
            data = self.caller(key.family, key.value, png)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {400, 401, 403, 404, 429, 500, 503}:
                self.pool.cooldown(key, seconds=300)
            raise
        return ExtractionResult(
            markdown=data.get("markdown", "UNKNOWN"), latex=data.get("latex", []), smiles=data.get("smiles", []),
            questions=data.get("questions", []), confidence=float(data.get("confidence", 0)), engine=f"api:{key.label}")

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
