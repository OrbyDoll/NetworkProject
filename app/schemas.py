from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TraceHopResponse(BaseModel):
    hop_number: int
    ip: Optional[str] = None
    hostname: Optional[str] = None
    delay: Optional[float] = None
    country: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

    class Config:
        from_attributes = True

class TraceRequestResponse(BaseModel):
    id: int
    target: str
    ip_address: Optional[str] = None
    created_at: datetime
    hops: List[TraceHopResponse] = []

    class Config:
        from_attributes = True

class TraceRequestCreate(BaseModel):
    target: str = Field(..., max_length=255)

class StatsResponse(BaseModel):
    total_traces: int
    avg_hops: float
    popular_targets: List[dict]
    requests_last_24h: int