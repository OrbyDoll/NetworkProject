import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class TraceRequest(Base):
    __tablename__ = "trace_requests"

    id = Column(Integer, primary_key=True, index=True)
    target = Column(String, index=True)
    ip_address = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    hops = relationship("TraceHop", back_populates="trace_request", cascade="all, delete-orphan")

class TraceHop(Base):
    __tablename__ = "trace_hops"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(Integer, ForeignKey("trace_requests.id"))
    hop_number = Column(Integer)
    ip = Column(String, nullable=True)
    hostname = Column(String, nullable=True)
    delay = Column(Float, nullable=True)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)

    trace_request = relationship("TraceRequest", back_populates="hops")