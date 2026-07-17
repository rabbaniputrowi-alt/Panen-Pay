"""Vision grading (R6): GPT-4o structured outputs when a key is present,
deterministic mock otherwise (§E). Off-enum or malformed output is retried,
never coerced.
"""

import base64
import hashlib
import io
import json
import time

from PIL import Image
from pydantic import ValidationError

from app.models import GradeResult

GRADING_SYSTEM_PROMPT = """You grade a single photo of harvested red chilies into exactly one of three tiers.

Rubric:
- fresh: glossy, taut skin; vivid, saturated red; firm-looking pods.
- sell_today: slight dulling of the skin, early softening or minor blemishes; still sellable but should move today.
- wilted: wrinkled or shriveled skin, darkened or dull color, limp pods.

Rules:
- Judge only what is visible in the photo.
- visual_evidence: one short sentence in Bahasa Indonesia naming the visible cues you used.
- If the photo is not chilies or is unusable, pick the closest tier and set confidence to "low".
"""

GRADE_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "grade_result",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "grade": {"type": "string", "enum": ["fresh", "sell_today", "wilted"]},
                "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                "visual_evidence": {"type": "string"},
            },
            "required": ["grade", "confidence", "visual_evidence"],
            "additionalProperties": False,
        },
    },
}

MAX_LONG_EDGE_PX = 1024

_MOCK_EVIDENCE = {
    "fresh": "Kulit tampak mengkilap dan kencang dengan warna merah cerah (penilaian simulasi).",
    "sell_today": "Warna mulai kusam dan kulit sedikit melunak (penilaian simulasi).",
    "wilted": "Kulit keriput dan warna menggelap, buah tampak lemas (penilaian simulasi).",
}

class GradingError(RuntimeError):
    """Grading failed after all retries. Routers map this to HTTP 502."""

def prepare_image_b64(image_bytes: bytes) -> str:
    """Downscale long edge to ≤1024px, re-encode as JPEG, return base64."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    long_edge = max(img.size)
    if long_edge > MAX_LONG_EDGE_PX:
        scale = MAX_LONG_EDGE_PX / long_edge
        img = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode("ascii")

class MockGrader:
    """§E keyless path: grade = SHA-256(image bytes) % 3, same schema and
    latency shape as the real call."""

    name = "mock"

    def __init__(self, latency_s: float = 0.8):
        self.latency_s = latency_s

    def grade(self, image_bytes: bytes) -> GradeResult:
        if self.latency_s:
            time.sleep(self.latency_s)
        h = int.from_bytes(hashlib.sha256(image_bytes).digest(), "big")
        grade = ("fresh", "sell_today", "wilted")[h % 3]
        confidence = ("high", "high", "medium", "low")[(h >> 8) % 4]
        return GradeResult(grade=grade, confidence=confidence, visual_evidence=_MOCK_EVIDENCE[grade])

class OpenAIGrader:
    name = "openai"
    MODEL = "gpt-4o"
    MAX_ATTEMPTS = 3

    def __init__(self, api_key: str):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)

    def grade(self, image_bytes: bytes) -> GradeResult:
        b64 = prepare_image_b64(image_bytes)
        messages = [
            {"role": "system", "content": GRADING_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"},
                    }
                ],
            },
        ]
        last_error = "no attempts made"
        for _ in range(self.MAX_ATTEMPTS):
            response = self._client.chat.completions.create(
                model=self.MODEL,
                temperature=0,
                response_format=GRADE_RESPONSE_FORMAT,
                messages=messages,
            )
            message = response.choices[0].message
            if getattr(message, "refusal", None):
                last_error = f"refusal: {message.refusal}"
                continue
            if not message.content:
                last_error = "empty completion"
                continue
            try:
                return GradeResult.model_validate(json.loads(message.content))
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = f"schema parse failure: {exc}"
                continue
        raise GradingError(f"grading failed after {self.MAX_ATTEMPTS} attempts: {last_error}")

def make_grader(api_key: str | None):
    return OpenAIGrader(api_key) if api_key else MockGrader()
