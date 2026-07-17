from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import get_store
from app.store import Store

router = APIRouter()

class WeightIngest(BaseModel):
    station_id: str = "station-1"
    weight_grams: float
    stable: bool

@router.post("/ingest/weight")
def ingest_weight(payload: WeightIngest, store: Store = Depends(get_store)) -> dict:
    state = store.get_station_state() or {}
    state.update(
        {
            "stationId": payload.station_id,
            "lastWeightGrams": payload.weight_grams,
            "stable": payload.stable,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }
    )
    state.setdefault("lastTier", None)
    state.setdefault("pendingGrade", None)
    store.set_station_state(state)
    return {"ok": True}
