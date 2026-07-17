import base64
from datetime import datetime

from app.services import certificate_svc, mock_ledger

def sample_tx() -> dict:
    return {
        "txId": "tx-0001",
        "farmerName": "Bu Sari",
        "tier": "fresh",
        "weightKg": 2.37,
        "pricePerKg": 40_000,
        "totalIdr": 94_800,
        "gps": {"lat": -7.797, "lng": 110.370},
        "createdAt": "2026-07-16T01:00:00+00:00",
        "status": "paid_mock",
    }

def test_hash_round_trip():
    tx = sample_tx()
    cert = certificate_svc.make_certificate(tx, base_url="http://localhost:8000")
    tx["certificateHash"] = cert["sha256"]
    assert certificate_svc.verify(tx, cert["sha256"])

def test_mutating_any_field_breaks_verify():
    tx = sample_tx()
    sha = certificate_svc.tx_sha256(tx)
    mutations = {
        "txId": "tx-9999",
        "farmerName": "Bu Sari ",
        "tier": "wilted",
        "weightKg": 2.38,
        "pricePerKg": 40_100,
        "totalIdr": 94_900,
        "gps": {"lat": -7.797, "lng": 110.371},
        "createdAt": "2026-07-16T01:00:01+00:00",
        "status": "paid",
    }
    for field, tampered_value in mutations.items():
        tampered = sample_tx()
        tampered[field] = tampered_value
        assert not certificate_svc.verify(tampered, sha), f"tampered {field} still verified"

def test_certificate_backrefs_excluded_from_hash():
    tx = sample_tx()
    sha = certificate_svc.tx_sha256(tx)
    tx["certificateHash"] = sha
    tx["certId"] = "abc123def456"
    assert certificate_svc.tx_sha256(tx) == sha

def test_qr_data_uri_is_png():
    cert = certificate_svc.make_certificate(sample_tx(), base_url="http://localhost:8000")
    prefix = "data:image/png;base64,"
    assert cert["qrPngDataUri"].startswith(prefix)
    raw = base64.b64decode(cert["qrPngDataUri"][len(prefix):])
    assert raw.startswith(b"\x89PNG\r\n\x1a\n")

def test_qr_payload_url_points_at_cert_page():
    cert = certificate_svc.make_certificate(sample_tx(), base_url="http://localhost:8000")
    assert cert["qrPayloadUrl"] == f"http://localhost:8000/cert/{cert['certId']}"

def test_mock_ledger_records_paid_mock():
    receipt = mock_ledger.record_payment("tx-0001", 94_800)
    assert receipt["status"] == "paid_mock"
    datetime.fromisoformat(receipt["paidAt"])
