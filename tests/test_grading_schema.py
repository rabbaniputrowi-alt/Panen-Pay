import io
import json
from types import SimpleNamespace

import pytest
from PIL import Image

from app.services import brief_writer
from app.services.brief_writer import (
    OpenAIBriefWriter,
    TemplateBriefWriter,
    allowed_digit_sequences,
    digits_ok,
    make_brief_writer,
    template_brief,
)
from app.services.vision_grader import (
    GradingError,
    MockGrader,
    OpenAIGrader,
    make_grader,
)

VALID_PAYLOAD = json.dumps(
    {"grade": "fresh", "confidence": "high", "visual_evidence": "Kulit mengkilap."}
)


def jpeg_bytes(color=(210, 30, 30)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color).save(buf, format="JPEG")
    return buf.getvalue()


class FakeChatCompletions:
    """Yields scripted responses; repeats the last one when exhausted."""

    def __init__(self, script):
        self._script = list(script)
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        item = self._script[min(self.calls - 1, len(self._script) - 1)]
        message = SimpleNamespace(content=item.get("content"), refusal=item.get("refusal"))
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def scripted_grader(script):
    grader = OpenAIGrader.__new__(OpenAIGrader)  # bypass __init__: no key, no network
    fake = FakeChatCompletions(script)
    grader._client = SimpleNamespace(chat=SimpleNamespace(completions=fake))
    return grader, fake


def scripted_brief_writer(script):
    writer = OpenAIBriefWriter.__new__(OpenAIBriefWriter)
    fake = FakeChatCompletions(script)
    writer._client = SimpleNamespace(chat=SimpleNamespace(completions=fake))
    return writer, fake


# --- grader retry semantics (R6) ---------------------------------------------


def test_off_enum_grade_rejected_after_retries():
    bad = json.dumps({"grade": "rotten", "confidence": "high", "visual_evidence": "x"})
    grader, fake = scripted_grader([{"content": bad}])
    with pytest.raises(GradingError):
        grader.grade(jpeg_bytes())
    assert fake.calls == OpenAIGrader.MAX_ATTEMPTS


def test_malformed_json_retried_then_raises():
    grader, fake = scripted_grader([{"content": "definitely } not json"}])
    with pytest.raises(GradingError):
        grader.grade(jpeg_bytes())
    assert fake.calls == OpenAIGrader.MAX_ATTEMPTS


def test_malformed_then_valid_succeeds_on_retry():
    grader, fake = scripted_grader(
        [{"content": "not json"}, {"content": "{"}, {"content": VALID_PAYLOAD}]
    )
    result = grader.grade(jpeg_bytes())
    assert result.grade == "fresh"
    assert fake.calls == 3


def test_refusal_retried_then_raises():
    grader, fake = scripted_grader([{"refusal": "I cannot help with that.", "content": None}])
    with pytest.raises(GradingError):
        grader.grade(jpeg_bytes())
    assert fake.calls == OpenAIGrader.MAX_ATTEMPTS


def test_empty_content_retried_then_raises():
    grader, fake = scripted_grader([{"content": ""}])
    with pytest.raises(GradingError):
        grader.grade(jpeg_bytes())
    assert fake.calls == OpenAIGrader.MAX_ATTEMPTS


# --- mock grader (§E) ---------------------------------------------------------


def test_mock_grader_deterministic():
    grader = MockGrader(latency_s=0)
    image = jpeg_bytes()
    first, second = grader.grade(image), grader.grade(image)
    assert first == second


def test_mock_grader_stays_on_enum():
    grader = MockGrader(latency_s=0)
    for seed in range(10):
        result = grader.grade(bytes([seed]) * 50)
        assert result.grade in {"fresh", "sell_today", "wilted"}
        assert result.confidence in {"high", "medium", "low"}
        assert result.visual_evidence


def test_make_grader_selects_by_key_presence():
    assert isinstance(make_grader(None), MockGrader)
    assert isinstance(make_grader("sk-test"), OpenAIGrader)
    assert isinstance(make_brief_writer(None), TemplateBriefWriter)
    assert isinstance(make_brief_writer("sk-test"), OpenAIBriefWriter)


# --- brief writer digit guard (R1) --------------------------------------------

PAYLOAD = {
    "farmerName": "Bu Sari",
    "tier": "sell_today",
    "weightKg": 2.37,
    "pricePerKg": 32_000,
    "totalIdr": 75_800,
}


def test_template_brief_passes_its_own_guard():
    allowed = allowed_digit_sequences(PAYLOAD)
    assert digits_ok(template_brief(PAYLOAD), allowed)


def test_digit_guard_accepts_formatted_restatements():
    allowed = allowed_digit_sequences(PAYLOAD)
    assert digits_ok("Total Rp75.800 untuk 2,37 kg (simulasi).", allowed)
    assert digits_ok("Harga Rp32000 per kg.", allowed)


def test_digit_guard_rejects_invented_numbers():
    allowed = allowed_digit_sequences(PAYLOAD)
    assert not digits_ok("Total Rp99.999 (simulasi).", allowed)
    assert not digits_ok("Sekitar 76000 rupiah.", allowed)


def test_brief_writer_falls_back_to_template_on_bad_digits():
    writer, fake = scripted_brief_writer([{"content": "Total Rp99.999."}])
    assert writer.write(PAYLOAD) == template_brief(PAYLOAD)
    assert fake.calls == OpenAIBriefWriter.MAX_ATTEMPTS


def test_brief_writer_returns_clean_llm_text():
    text = "Setoran Bu Sari: 2,37 kg cabai, total Rp75.800 (pembayaran simulasi)."
    writer, fake = scripted_brief_writer([{"content": text}])
    assert writer.write(PAYLOAD) == text
    assert fake.calls == 1
