"""Certificate issuance: canonical-JSON SHA-256 over the transaction + QR PNG.

The hash covers every transaction field EXCEPT the certificate back-references
(``certificateHash``, ``certId``), which are written onto the record only
after the hash is computed.
"""

import base64
import hashlib
import io
import json
import os
import uuid
from datetime import datetime, timezone

import qrcode

_HASH_EXCLUDED_FIELDS = {"certificateHash", "certId"}

def _canonical_json(payload: dict) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    ).encode("utf-8")

def tx_sha256(tx: dict) -> str:
    hashable = {k: v for k, v in tx.items() if k not in _HASH_EXCLUDED_FIELDS}
    return hashlib.sha256(_canonical_json(hashable)).hexdigest()

def make_certificate(tx: dict, base_url: str | None = None) -> dict:
    base = (base_url or os.environ.get("PANEN_BASE_URL", "http://localhost:8000")).rstrip("/")
    cert_id = uuid.uuid4().hex[:12]
    qr_payload_url = f"{base}/cert/{cert_id}"

    img = qrcode.make(qr_payload_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_png_data_uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

    return {
        "certId": cert_id,
        "txId": tx["txId"],
        "sha256": tx_sha256(tx),
        "qrPayloadUrl": qr_payload_url,
        "issuedAt": datetime.now(timezone.utc).isoformat(),
        "qrPngDataUri": qr_png_data_uri,
    }

def verify(tx: dict, sha256: str) -> bool:
    return tx_sha256(tx) == sha256
