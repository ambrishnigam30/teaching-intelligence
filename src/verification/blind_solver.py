"""Cross-family blind solving and independent question verification."""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from typing import Callable, Protocol

import httpx
from src.rotator.key_pool import KeyPool, QuotaExhausted

BLIND_SOLVER_PROMPT = """You are an elite JEE Advanced and JEE Main solver.
Solve the following question step by step from first principles.
Identify any traps, verify units and dimensions, and state the exact final answer.
Format your final answer on the last line as:
FINAL ANSWER: <answer>
where <answer> is the option letter (A, B, C, or D), numerical value, or matrix match tuple."""

@dataclass
class BlindSolveResult:
    question_id: str
    solver_provider: str
    solver_family: str
    predicted_answer: str
    reasoning: str
    confidence: float = 0.85

class BlindSolverCaller(Protocol):
    def __call__(self, family: str, key: str, prompt: str) -> str: ...

class HttpBlindSolverCaller:
    def __call__(self, family: str, key: str, prompt: str) -> str:
        if family == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = httpx.post(url, json=payload, timeout=60)
            res.raise_for_status()
            return res.json()["candidates"][0]["content"]["parts"][0]["text"]
        elif family == "groq":
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {key}"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            }
            res = httpx.post(url, headers=headers, json=payload, timeout=60)
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]
        else:  # openrouter
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {"Authorization": f"Bearer {key}"}
            payload = {
                "model": "google/gemma-3-27b-it:free",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            }
            res = httpx.post(url, headers=headers, json=payload, timeout=60)
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]

class BlindSolver:
    """Solves questions independently using a provider family strictly isolated from the transcription family."""

    def __init__(self, pool: KeyPool, caller: BlindSolverCaller | None = None):
        self.pool = pool
        self.caller = caller or HttpBlindSolverCaller()

    @staticmethod
    def extract_final_answer(text: str) -> str:
        """Extract the final answer token from solver reasoning output."""
        # Check for explicit "FINAL ANSWER: <ans>"
        m = re.search(r"FINAL\s*ANSWER\s*[:=]\s*([A-D](?:\s*,\s*[A-D])*|-?[0-9]+(?:\.[0-9]+)?|[A-D])\b", text, re.IGNORECASE)
        if m:
            return m.group(1).strip().upper()
        # Fallback to last line containing Option (X) or Answer: X
        last_lines = "\n".join(text.strip().splitlines()[-5:])
        m_opt = re.search(r"(?:Correct\s+Option|Answer|Option)\s*[:=]?\s*\(?([A-D])\)?", last_lines, re.IGNORECASE)
        if m_opt:
            return m_opt.group(1).strip().upper()
        return "UNKNOWN"

    def solve(self, question: dict, transcription_family: str) -> BlindSolveResult:
        """Solves a question while guaranteeing cross-family isolation."""
        qid = question.get("question_id", "q_unknown")
        stem = question.get("stem", "")
        options = question.get("options", [])
        opt_text = "\n".join(f"({chr(65+i)}) {opt}" if not opt.startswith("(") else opt for i, opt in enumerate(options))

        user_prompt = f"{BLIND_SOLVER_PROMPT}\n\nQuestion:\n{stem}"
        if opt_text:
            user_prompt += f"\n\nOptions:\n{opt_text}"

        # Acquire a key from a DIFFERENT provider family
        author_fam = transcription_family.split("_", 1)[0].lower()
        key = self.pool.acquire(exclude_family=author_fam)
        try:
            raw_output = self.caller(key.family, key.value, user_prompt)
            answer = self.extract_final_answer(raw_output)
            return BlindSolveResult(
                question_id=qid,
                solver_provider=f"{key.family}_{key.index}",
                solver_family=key.family,
                predicted_answer=answer,
                reasoning=raw_output,
                confidence=0.9 if answer != "UNKNOWN" else 0.4,
            )
        except Exception:
            self.pool.cooldown(key, seconds=60)
            raise
