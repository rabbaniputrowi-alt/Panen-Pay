from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/healthz")
def healthz(request: Request) -> dict:
    return {
        "ok": True,
        "grader": request.app.state.grader.name,
        "store": request.app.state.store.name,
    }
