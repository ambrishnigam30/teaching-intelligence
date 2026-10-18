from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import base64
import json
from pathlib import Path
from typing import Protocol
import re

import os
import re

import httpx
from src.rotator.key_pool import KeyPool, QuotaExhausted

VISION_PROMPT = """Transcribe this JEE/NEET teaching page faithfully. Return JSON with markdown, latex, smiles, questions, diagrams.
Always provide the complete page text in 'markdown' with proper LaTeX for math formulas ($...$ or $$...$$).
For any questions found on the page, include them in 'questions' with:
- 'question_number': string (e.g. '1', 'Q.2')
- 'stem': string containing the complete question text, conditions, and formulas
- 'options': array of full option strings (e.g. ['(A) option 1', '(B) option 2', ...]) if multiple choice
- 'question_type': 'SINGLE_CHOICE' | 'MULTIPLE_CHOICE' | 'NUMERICAL' | 'SUBJECTIVE'
Never invent unreadable content; use UNKNOWN only if completely illegible."""
GEMINI_VISION_MODELS = ("gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash")
GROQ_VISION_MODELS = ("meta-llama/llama-4-scout-17b-16e-instruct", "meta-llama/llama-4-maverick-17b-128e-instruct")
GROQ_TEXT_MODELS = ("llama-3.3-70b-versatile", "qwen/qwen3-32b")
OPENROUTER_VISION_MODELS = (
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3.5-super-vl:free",
    "dots-studio/dots-3-note-preview:free",
    "qwen/qwen2.5-vl-72b-instruct:free",
    "openrouter/free",
)

def _prepare_image_bytes(png: bytes, max_bytes: int = 3_000_000) -> tuple[str, str]:
    if len(png) <= max_bytes:
        return "image/png", base64.b64encode(png).decode("ascii")
    try:
        import fitz
        pix = fitz.Pixmap(png)
        if pix.alpha:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        jpg = pix.tobytes("jpeg")
        if len(jpg) <= max_bytes:
            return "image/jpeg", base64.b64encode(jpg).decode("ascii")
        try:
            from PIL import Image
            img = Image.open(BytesIO(jpg))
            scale = 0.75
            while len(jpg) > max_bytes and scale >= 0.25:
                w, h = max(1, int(img.width * scale)), max(1, int(img.height * scale))
                resized = img.resize((w, h), Image.Resampling.LANCZOS)
                buf = BytesIO()
                resized.save(buf, format="JPEG", quality=75)
                jpg = buf.getvalue()
                scale -= 0.25
        except Exception:
            pass
        return "image/jpeg", base64.b64encode(jpg).decode("ascii")
    except Exception:
        return "image/png", base64.b64encode(png).decode("ascii")

def _parse_json_payload(raw_text: str) -> dict:
    text = raw_text.strip()
    if "```" in text:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            text = match.group(1).strip()
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end+1]
    data = json.loads(text)
    if not isinstance(data, dict):
        data = {"markdown": str(data)}
    markdown = data.get("markdown") or "UNKNOWN"
    latex = data.get("latex") or []
    if not isinstance(latex, list): latex = [str(latex)]
    smiles = data.get("smiles") or []
    if not isinstance(smiles, list): smiles = [str(smiles)]
    questions = data.get("questions") or []
    if not isinstance(questions, list): questions = []
    diagrams = data.get("diagrams") or []
    if not isinstance(diagrams, list): diagrams = []
    conf = data.get("confidence")
    if conf is None or conf == 0:
        confidence = 0.85 if (markdown != "UNKNOWN" or questions) else 0.5
    else:
        try:
            confidence = float(conf)
        except (ValueError, TypeError):
            confidence = 0.85
    valid_q = [q for q in questions if isinstance(q, dict)]
    # Safeguard 3: If questions are missing or all stems are empty, reconstruct from markdown
    if markdown and markdown != "UNKNOWN" and (not valid_q or all(not str(q.get("stem", "")).strip() for q in valid_q)):
        try:
            from src.extraction.question_parser import parse_questions_from_text
            reconstructed = parse_questions_from_text(str(markdown))
            if reconstructed:
                valid_q = reconstructed
        except Exception:
            pass

    return {
        "markdown": str(markdown),
        "latex": [str(x) for x in latex],
        "smiles": [str(x) for x in smiles],
        "questions": valid_q,
        "diagrams": diagrams,
        "confidence": confidence,
    }


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
        if family == "openrouter":
            for model in payload:
                mid = model.get("id", "")
                modalities = model.get("architecture", {}).get("input_modalities", [])
                if mid.endswith(":free") and "image" in modalities:
                    return mid
            for model in payload:
                if "image" in model.get("architecture", {}).get("input_modalities", []):
                    return model["id"]
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
        last_response: httpx.Response | None = None
        retryable_codes = {400, 402, 404, 408, 413, 422, 429, 500, 502, 503, 504}
        for dynamic in (False, True):
            for model in models:
                try:
                    response = httpx.post(f"{base}/models/{model}:generateContent", headers=headers, json=payload, timeout=75)
                    last_response = response
                    if response.status_code in {429, 401, 403}:
                        # Account-level quota exhaustion or auth: rotate key immediately
                        break
                    if response.status_code in retryable_codes:
                        continue
                    response.raise_for_status()
                    candidate_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                    return _parse_json_payload(candidate_text)
                except (httpx.TransportError, json.JSONDecodeError, KeyError, IndexError):
                    continue
            if dynamic or (last_response is not None and last_response.status_code in {429, 401, 403}):
                break
            try:
                models = [self._choose_dynamic_model(httpx.get(f"{base}/models", headers=headers, timeout=20), "gemini")]
            except Exception:
                break
        if last_response is not None:
            last_response.raise_for_status()
        raise RuntimeError("Gemini model fallback exhausted")

    def _openai_compatible(self, endpoint: str, models_endpoint: str, key: str, models: tuple[str, ...], parts: list[dict], family: str) -> dict:
        headers = {"Authorization": "Bearer " + key}
        content = [{"type": "text", "text": VISION_PROMPT + "\n\nPDF text clue:\n" + parts[0]["text"]}, {"type": "image_url", "image_url": {"url": parts[1]["inline_data"]["data"]}}]
        payload = {"response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": content}]}
        candidates = list(models)
        last_response: httpx.Response | None = None
        retryable_codes = {400, 402, 404, 408, 413, 422, 429, 500, 502, 503, 504}
        for dynamic in (False, True):
            for model in candidates:
                try:
                    response = httpx.post(endpoint, headers=headers, json={**payload, "model": model}, timeout=75)
                    last_response = response
                    if response.status_code in {429, 401, 403}:
                        # Account-level quota exhaustion or auth: rotate key immediately
                        break
                    if response.status_code in retryable_codes:
                        continue
                    response.raise_for_status()
                    message_text = response.json()["choices"][0]["message"]["content"]
                    return _parse_json_payload(message_text)
                except (httpx.TransportError, json.JSONDecodeError, KeyError, IndexError):
                    continue
            if dynamic or (last_response is not None and last_response.status_code in {429, 401, 403}):
                break
            try:
                listing = httpx.get(models_endpoint, headers=headers, timeout=20)
                listing.raise_for_status()
                candidates = [self._choose_dynamic_model(listing, family)]
            except Exception:
                break
        if last_response is not None:
            last_response.raise_for_status()
        raise RuntimeError(f"{family} model fallback exhausted")

    def __call__(self, family: str, key: str, png: bytes, text_clue: str = "") -> dict:
        mime, image = _prepare_image_bytes(png)
        parts = [{"text": VISION_PROMPT + "\n\nPDF text clue:\n" + text_clue[:12000]}, {"inline_data": {"mime_type": mime, "data": image}}]
        if family == "gemini":
            return self._gemini(key, parts)
        encoded_parts = [parts[0], {"inline_data": {"data": f"data:{mime};base64," + image}}]
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
    def render_page(document_path: Path, page_number: int, dpi: int = 300, source_file_id: str = "doc") -> tuple[bytes, list[bytes], str]:
        """Render one PDF page and extract both raster and vector diagram assets."""
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PyMuPDF is required for visual extraction; install the vision extra") from exc
        from src.extraction.vector_diagrams import extract_page_diagrams
        document = fitz.open(document_path)
        try:
            page = document[page_number]
            pixmap = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
            diagram_assets = extract_page_diagrams(document, page_number, source_file_id, dpi=dpi)
            diagram_bytes = [d.image_bytes for d in diagram_assets]
            if not diagram_bytes:
                for image in page.get_images(full=True):
                    extracted = document.extract_image(image[0])
                    if extracted.get("width", 0) >= 64 and extracted.get("height", 0) >= 64:
                        diagram_bytes.append(extracted["image"])
            return pixmap.tobytes("png"), diagram_bytes, page.get_text("text")
        finally:
            document.close()

    @staticmethod
    def render_page_with_assets(document_path: Path, page_number: int, source_file_id: str = "doc", dpi: int = 300) -> tuple[bytes, list, str]:
        """Render PDF page returning full DiagramAsset objects with 2D bounding boxes."""
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PyMuPDF is required for visual extraction; install the vision extra") from exc
        from src.extraction.vector_diagrams import extract_page_diagrams
        document = fitz.open(document_path)
        try:
            page = document[page_number]
            pixmap = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
            diagram_assets = extract_page_diagrams(document, page_number, source_file_id, dpi=dpi)
            return pixmap.tobytes("png"), diagram_assets, page.get_text("text")
        finally:
            document.close()

    def extract_ollama(self, png: bytes, text_clue: str = "") -> ExtractionResult | None:
        if os.getenv("ENABLE_LOCAL_OLLAMA", "").lower() not in {"1", "true", "yes"}:
            return None
        host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        models_str = os.getenv("OLLAMA_VISION_MODELS", "qwen2.5vl:7b,qwen2.5vl:3b,moondream")
        models = [m.strip() for m in models_str.split(",") if m.strip()]
        _mime, b64_img = _prepare_image_bytes(png)
        prompt = VISION_PROMPT + "\n\nPDF text clue:\n" + text_clue[:12000]
        for model in models:
            payload = {
                "model": model,
                "stream": False,
                "format": "json",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [b64_img],
                    }
                ],
            }
            try:
                response = httpx.post(f"{host}/api/chat", json=payload, timeout=180)
                if response.status_code == 200:
                    content = response.json().get("message", {}).get("content", "")
                    data = _parse_json_payload(content)
                    return ExtractionResult(
                        markdown=data.get("markdown", "UNKNOWN"),
                        latex=data.get("latex", []),
                        smiles=data.get("smiles", []),
                        questions=data.get("questions", []),
                        confidence=float(data.get("confidence", 0.82)),
                        engine=f"local:ollama:{model}",
                    )
            except Exception:
                continue
        return None

    def extract_png(self, png: bytes, author_family: str | None = None, text_clue: str = "") -> ExtractionResult:
        last_error: Exception | None = None
        for _ in range(len(self.pool.keys)):
            try:
                key = self.pool.acquire(exclude_family=author_family)
            except QuotaExhausted:
                break
            try:
                try:
                    data = self.caller(key.family, key.value, png, text_clue)
                except TypeError:  # Supports pre-existing three-argument test callers.
                    data = self.caller(key.family, key.value, png)
                return ExtractionResult(
                    markdown=data.get("markdown", "UNKNOWN"),
                    latex=data.get("latex", []),
                    smiles=data.get("smiles", []),
                    questions=data.get("questions", []),
                    confidence=float(data.get("confidence", 0)),
                    engine=f"api:{key.label}",
                )
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code in {429, 503}:
                    self.pool.cooldown(key, seconds=45)
                elif exc.response.status_code in {401, 403}:
                    self.pool.cooldown(key, seconds=120)
                else:
                    self.pool.cooldown(key, seconds=60)
            except (httpx.TransportError, json.JSONDecodeError, KeyError, RuntimeError) as exc:
                last_error = exc
                self.pool.cooldown(key, seconds=60)

        # 1. Server-installed local Ollama fallback if enabled
        if os.getenv("ENABLE_LOCAL_OLLAMA", "").lower() in {"1", "true", "yes"}:
            try:
                ollama_result = self.extract_ollama(png, text_clue)
                if ollama_result is not None:
                    return ollama_result
            except Exception:
                pass

        if last_error:
            raise last_error
        raise QuotaExhausted("No visual extraction engine (cloud Vision API or local Ollama) is available; pausing for next quota window")

    @staticmethod
    def text_fallback(text: str) -> ExtractionResult:
        readable = " ".join(text.split())
        latex = re.findall(r"\$([^$]+)\$|\\\(([^)]+)\\\)", text)
        expressions = [a or b for a, b in latex]
        questions = [{"stem": line.strip()} for line in text.splitlines() if re.match(r"^\s*(?:Q(?:uestion)?\s*)?\d+[.)]", line, re.I)]
        if not questions:
            try:
                from src.extraction.question_parser import parse_questions_from_text
                questions = parse_questions_from_text(text)
            except Exception:
                questions = []
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
