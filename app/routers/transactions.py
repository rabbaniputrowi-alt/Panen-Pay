import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import Settings
from app.deps import get_brief_writer, get_settings, get_store
from app.models import GPS
from app.services import certificate_svc, mock_ledger
from app.services.pricing_engine import price_per_kg, total_idr
from app.store import Store

router = APIRouter()


class TransactionRequest(BaseModel):
    farmerName: str
    gps: GPS
    stationId: str = "station-1"


@router.post("/transactions")
def create_transaction(
    payload: TransactionRequest,
    store: Store = Depends(get_store),
    brief_writer=Depends(get_brief_writer),
    settings: Settings = Depends(get_settings),
) -> dict:
    state = store.get_station_state() or {}
    if not state.get("stable"):
        raise HTTPException(status_code=409, detail="no stable weight on the scale")
    pending = state.get("pendingGrade")
    if not pending:
        raise HTTPException(status_code=409, detail="no pending grade — photograph the batch first")

    tier = pending["grade"]
    weight_kg = round(float(state["lastWeightGrams"]) / 1000, 3)
    try:
        per_kg = price_per_kg(tier)
        total = total_idr(tier, weight_kg)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    tx_id = "tx-" + uuid.uuid4().hex[:10]
    payment = mock_ledger.record_payment(tx_id, total)
    tx = {
        "txId": tx_id,
        "farmerName": payload.farmerName,
        "tier": tier,
        "weightKg": weight_kg,
        "pricePerKg": per_kg,
        "totalIdr": total,
        "gps": payload.gps.model_dump(),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "grade": pending,
        "status": payment["status"],
        "paidAt": payment["paidAt"],
    }
    cert = certificate_svc.make_certificate(tx, base_url=settings.PANEN_BASE_URL)
    tx["certificateHash"] = cert["sha256"]
    tx["certId"] = cert["certId"]

    store.put_transaction(tx)
    store.put_certificate(cert)

    brief = brief_writer.write(
        {
            "farmerName": payload.farmerName,
            "tier": tier,
            "weightKg": weight_kg,
            "pricePerKg": per_kg,
            "totalIdr": total,
        }
    )

    # Consume the pending grade and queue the station buzzer tone.
    state["pendingGrade"] = None
    state["updatedAt"] = datetime.now(timezone.utc).isoformat()
    store.set_station_state(state)
    store.set_feedback(payload.stationId, tier)

    return {"transaction": tx, "certificate": cert, "brief": brief}


@router.get("/transactions/recent")
def recent_transactions(store: Store = Depends(get_store)) -> dict:
    return {"transactions": store.list_recent_transactions(25)}
