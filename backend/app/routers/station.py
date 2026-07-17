from fastapi import APIRouter, Depends

from app.deps import get_store
from app.store import Store

router = APIRouter()

@router.get("/station/feedback")
def station_feedback(station_id: str = "station-1", store: Store = Depends(get_store)) -> dict:
    return {"tone": store.pop_feedback(station_id)}

@router.get("/station/state")
def station_state(store: Store = Depends(get_store)) -> dict:
    return {"state": store.get_station_state()}
