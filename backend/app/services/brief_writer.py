"""Bahasa Indonesia transaction briefs.

R1 enforcement: the LLM only restates numbers computed by the pricing engine.
Every digit sequence in its output must already exist in the input payload;
otherwise the brief is rejected, retried once, then replaced by the template.
Prose never blocks the flow.
"""

import json
import re

BRIEF_SYSTEM_PROMPT = (
    "Tulis satu ringkasan transaksi singkat (maksimal 2 kalimat) dalam Bahasa Indonesia "
    "untuk setoran cabai petani, berdasarkan data JSON yang diberikan. "
    "Sebutkan ulang angka persis seperti pada data — tanpa pemisah ribuan, tanpa pembulatan, "
    "dan jangan pernah menghitung angka baru. Sebutkan bahwa pembayaran adalah simulasi."
)

TIER_LABEL_ID = {"fresh": "segar", "sell_today": "jual hari ini", "wilted": "layu"}


def template_brief(payload: dict) -> str:
    """Keyless / fallback brief: filled purely from engine numbers."""
    return (
        f"Setoran {payload['farmerName']} tercatat: {payload['weightKg']} kg cabai "
        f"grade {TIER_LABEL_ID[payload['tier']]}. Harga Rp{payload['pricePerKg']}/kg, "
        f"total Rp{payload['totalIdr']} (pembayaran simulasi)."
    )


def allowed_digit_sequences(payload: dict) -> set[str]:
    return set(re.findall(r"\d+", json.dumps(payload, ensure_ascii=False, default=str)))


def digits_ok(text: str, allowed: set[str]) -> bool:
    """Every number token in the text must reduce to digits from the payload.

    A token passes if its digits joined (thousands separators stripped, e.g.
    "94.800" -> "94800") are an allowed sequence, or if every separator-split
    part (decimal style, e.g. "2,37" -> "2" + "37") is allowed.
    """
    for token in re.findall(r"\d[\d.,]*\d|\d", text):
        joined = re.sub(r"[.,]", "", token)
        parts = [p for p in re.split(r"[.,]", token) if p]
        if joined in allowed:
            continue
        if parts and all(p in allowed for p in parts):
            continue
        return False
    return True


class TemplateBriefWriter:
    name = "template"

    def write(self, payload: dict) -> str:
        return template_brief(payload)


class OpenAIBriefWriter:
    name = "openai"
    MODEL = "gpt-4o"
    MAX_ATTEMPTS = 2  # first call + one retry, then template fallback

    def __init__(self, api_key: str):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)

    def write(self, payload: dict) -> str:
        allowed = allowed_digit_sequences(payload)
        user_content = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        for _ in range(self.MAX_ATTEMPTS):
            try:
                response = self._client.chat.completions.create(
                    model=self.MODEL,
                    temperature=0,
                    messages=[
                        {"role": "system", "content": BRIEF_SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                )
            except Exception:
                break  # API trouble -> template, never block the flow on prose
            text = (response.choices[0].message.content or "").strip()
            if text and digits_ok(text, allowed):
                return text
        return template_brief(payload)


def make_brief_writer(api_key: str | None):
    return OpenAIBriefWriter(api_key) if api_key else TemplateBriefWriter()
