"""Deliberately a stub (R3): every payment is simulated, no money ever moves."""

from datetime import datetime, timezone

def record_payment(tx_id: str, total_idr: int) -> dict:
    return {"status": "paid_mock", "paidAt": datetime.now(timezone.utc).isoformat()}
