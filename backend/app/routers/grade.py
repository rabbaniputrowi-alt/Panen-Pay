from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.deps import get_grader, get_store
from app.models import GradeResult
from app.services.vision_grader import GradingError
from app.store import Store

router = APIRouter()

@router.post("/grade", response_model=GradeResult)
async def grade_photo(
    photo: UploadFile = File(...),
    store: Store = Depends(get_store),
    grader=Depends(get_grader),
) -> GradeResult:
    image_bytes = await photo.read()
    if not image_bytes:
        raise HTTPException(status_code=422, detail="empty photo upload")
    try:
        result = grader.grade(image_bytes)
    except GradingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    state = store.get_station_state() or {}
    state.update(
        {
            "lastTier": result.grade,
            "pendingGrade": result.model_dump(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }
    )
    state.setdefault("lastWeightGrams", 0.0)
    state.setdefault("stable", False)
    store.set_station_state(state)
    return result
