from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from app.config import Settings
from app.deps import get_settings, get_store
from app.services import certificate_svc
from app.store import Store

router = APIRouter()

redirect_router = APIRouter()

@redirect_router.get("/cert/{cert_id}")
def cert_redirect(cert_id: str, settings: Settings = Depends(get_settings)):
    base = settings.FRONTEND_BASE_URL.rstrip("/")
    return RedirectResponse(f"{base}/cert/{cert_id}", status_code=307)

@router.get("/certificates/{cert_id}")
def get_certificate(
    cert_id: str, verify: int = 0, store: Store = Depends(get_store)
) -> dict:
    cert = store.get_certificate(cert_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="unknown certificate")
    tx = store.get_transaction(cert["txId"])
    if tx is None:
        raise HTTPException(status_code=404, detail="certificate has no transaction")

    response = {"certificate": cert, "transaction": tx}
    if verify:
        response["valid"] = certificate_svc.verify(tx, cert["sha256"])
    return response
