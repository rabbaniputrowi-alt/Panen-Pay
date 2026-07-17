from typing import Literal, Optional

from pydantic import BaseModel

Tier = Literal["fresh", "sell_today", "wilted"]

class GPS(BaseModel):
    lat: float
    lng: float

class Transaction(BaseModel):
    txId: str
    farmerName: str
    tier: Tier
    weightKg: float
    pricePerKg: int
    totalIdr: int
    gps: GPS
    createdAt: str
    certificateHash: str
    status: str = "paid_mock"

class Certificate(BaseModel):
    certId: str
    txId: str
    sha256: str
    qrPayloadUrl: str
    issuedAt: str
    qrPngDataUri: Optional[str] = None

class StationState(BaseModel):
    lastWeightGrams: float
    stable: bool
    lastTier: Optional[Tier] = None
    updatedAt: str

class GradeResult(BaseModel):
    grade: Tier
    confidence: Literal["high", "medium", "low"]
    visual_evidence: str
