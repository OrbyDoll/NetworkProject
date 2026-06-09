from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List
from datetime import datetime, timedelta

from ..database import get_db
from ..models import TraceRequest, TraceHop
from ..schemas import TraceRequestCreate, TraceRequestResponse, StatsResponse
from ..services.traceroute import run_traceroute, resolve_dns, is_valid_target

router = APIRouter()

@router.post("/api/traceroute", response_model=TraceRequestResponse)
async def perform_traceroute(request: TraceRequestCreate, db: AsyncSession = Depends(get_db)):
    target = request.target.strip()
    
    if not is_valid_target(target):
        raise HTTPException(status_code=400, detail="Invalid domain or IP format.")
        
    ip_address = resolve_dns(target)
    if not ip_address:
        raise HTTPException(status_code=400, detail="Could not resolve DNS for target.")
        
    try:
        hops_data = await run_traceroute(ip_address)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    new_trace = TraceRequest(target=target, ip_address=ip_address)
    db.add(new_trace)
    await db.flush()
    
    for hop in hops_data:
        new_hop = TraceHop(
            trace_id=new_trace.id,
            hop_number=hop["hop_number"],
            ip=hop["ip"] if hop["ip"] != "-" else None,
            hostname=hop["hostname"] if hop["hostname"] != "-" else None,
            delay=hop["delay"] if hop["delay"] > 0 else None,
            country=hop["country"] if hop["country"] != "-" else None,
            city=hop["city"] if hop["city"] != "-" else None,
            lat=hop["lat"],
            lon=hop["lon"]
        )
        db.add(new_hop)
        
    await db.commit()
    await db.refresh(new_trace)
    
    # We load manually to satisfy response_model
    stmt = select(TraceHop).where(TraceHop.trace_id == new_trace.id).order_by(TraceHop.hop_number)
    result = await db.execute(stmt)
    new_trace.hops = result.scalars().all()
    
    return new_trace

@router.get("/api/history", response_model=List[TraceRequestResponse])
async def get_history(db: AsyncSession = Depends(get_db)):
    stmt = select(TraceRequest).order_by(desc(TraceRequest.created_at)).limit(50)
    result = await db.execute(stmt)
    traces = result.scalars().all()
    
    # Eager loading manually for simplicity or use options
    for trace in traces:
        hop_stmt = select(TraceHop).where(TraceHop.trace_id == trace.id).order_by(TraceHop.hop_number)
        hop_res = await db.execute(hop_stmt)
        trace.hops = hop_res.scalars().all()
        
    return traces

@router.get("/api/history/{id}", response_model=TraceRequestResponse)
async def get_history_detail(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(TraceRequest).where(TraceRequest.id == id)
    result = await db.execute(stmt)
    trace = result.scalars().first()
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
        
    hop_stmt = select(TraceHop).where(TraceHop.trace_id == trace.id).order_by(TraceHop.hop_number)
    hop_res = await db.execute(hop_stmt)
    trace.hops = hop_res.scalars().all()
    
    return trace

@router.get("/api/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    # Total traces
    total_res = await db.execute(select(func.count(TraceRequest.id)))
    total_traces = total_res.scalar() or 0
    
    # Avg hops
    avg_hops_res = await db.execute(select(func.avg(TraceHop.hop_number)))
    avg_hops = avg_hops_res.scalar() or 0.0
    
    # Popular targets
    pop_stmt = select(TraceRequest.target, func.count(TraceRequest.target).label('count')).group_by(TraceRequest.target).order_by(desc('count')).limit(5)
    pop_res = await db.execute(pop_stmt)
    popular_targets = [{"target": row.target, "count": row.count} for row in pop_res.all()]
    
    # Last 24h
    time_24h_ago = datetime.utcnow() - timedelta(days=1)
    last_24h_stmt = select(func.count(TraceRequest.id)).where(TraceRequest.created_at >= time_24h_ago)
    last_24h_res = await db.execute(last_24h_stmt)
    requests_last_24h = last_24h_res.scalar() or 0
    
    return {
        "total_traces": total_traces,
        "avg_hops": round(avg_hops, 2),
        "popular_targets": popular_targets,
        "requests_last_24h": requests_last_24h
    }