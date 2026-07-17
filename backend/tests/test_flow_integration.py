import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings
from app.main import create_app
from app.services.pricing_engine import total_idr
from app.services.vision_grader import MockGrader

TIERS = {"fresh", "sell_today", "wilted"}

@pytest.fixture()
def client():
    settings = Settings(
        OPENAI_API_KEY=None,
        FIREBASE_SERVICE_ACCOUNT_JSON=None,
        PANEN_BASE_URL="http://localhost:8000",
        _env_file=None,
    )
    app = create_app(settings)
    app.state.grader = MockGrader(latency_s=0)
    with TestClient(app) as test_client:
        yield test_client

def red_jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (128, 128), (203, 22, 22)).save(buf, format="JPEG")
    return buf.getvalue()

def test_healthz_reports_keyless_adapters(client):
    for path in ("/healthz", "/api/v1/healthz"):
        body = client.get(path).json()
        assert body == {"ok": True, "grader": "mock", "store": "memory"}

def test_transaction_requires_stable_weight_and_grade(client):
    tx_req = {"farmerName": "Bu Sari", "gps": {"lat": -7.79, "lng": 110.37}}
    assert client.post("/api/v1/transactions", json=tx_req).status_code == 409

    client.post(
        "/api/v1/ingest/weight",
        json={"station_id": "station-1", "weight_grams": 2400, "stable": True},
    )
    assert client.post("/api/v1/transactions", json=tx_req).status_code == 409

def test_full_station_flow(client):
    resp = client.post(
        "/api/v1/ingest/weight",
        json={"station_id": "station-1", "weight_grams": 2400, "stable": True},
    )
    assert resp.status_code == 200

    resp = client.post(
        "/api/v1/grade", files={"photo": ("chili.jpg", red_jpeg(), "image/jpeg")}
    )
    assert resp.status_code == 200
    grade = resp.json()
    assert grade["grade"] in TIERS

    resp = client.post(
        "/api/v1/transactions",
        json={"farmerName": "Bu Sari", "gps": {"lat": -7.79, "lng": 110.37}},
    )
    assert resp.status_code == 200
    body = resp.json()
    tx, cert = body["transaction"], body["certificate"]
    assert tx["tier"] == grade["grade"]
    assert tx["weightKg"] == 2.4
    assert tx["totalIdr"] == total_idr(grade["grade"], 2.4)
    assert tx["status"] == "paid_mock"
    assert str(tx["totalIdr"]) in body["brief"]

    recent = client.get("/api/v1/transactions/recent").json()["transactions"]
    assert recent[0]["txId"] == tx["txId"]

    verified = client.get(f"/api/v1/certificates/{cert['certId']}?verify=1").json()
    assert verified["valid"] is True
    assert verified["transaction"]["txId"] == tx["txId"]

    feedback_url = "/api/v1/station/feedback?station_id=station-1"
    assert client.get(feedback_url).json()["tone"] == tx["tier"]
    assert client.get(feedback_url).json()["tone"] == "none"

    assert (
        client.post(
            "/api/v1/transactions",
            json={"farmerName": "Pak Budi", "gps": {"lat": -7.79, "lng": 110.37}},
        ).status_code
        == 409
    )

def test_unknown_certificate_404(client):
    assert client.get("/api/v1/certificates/nope?verify=1").status_code == 404
