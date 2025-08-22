"""
Transportation management database models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, Time, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class Vehicle(Base):
    """Vehicle for school transportation"""
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    registration_number = Column(String(50), nullable=False, unique=True)
    capacity = Column(Integer, nullable=False)
    driver_name = Column(String(100), nullable=True)
    driver_phone = Column(String(20), nullable=True)
    insurance_expiry = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)
    route = relationship("Route", back_populates="vehicles")

    def __repr__(self):
        return f"<Vehicle(id={self.id}, registration_number='{self.registration_number}')>"


class Route(Base):
    """Transport routes"""
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    stops = relationship("Stop", back_populates="route", cascade="all, delete-orphan")
    vehicles = relationship("Vehicle", back_populates="route")
    transport_members = relationship("TransportMember", back_populates="route")

    def __repr__(self):
        return f"<Route(id={self.id}, name='{self.name}')>"


class Stop(Base):
    """Stops along a transport route"""
    __tablename__ = "stops"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    arrival_time_am = Column(Time, nullable=True)
    departure_time_am = Column(Time, nullable=True)
    arrival_time_pm = Column(Time, nullable=True)
    departure_time_pm = Column(Time, nullable=True)
    
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    route = relationship("Route", back_populates="stops")
    
    transport_members = relationship("TransportMember", back_populates="stop")

    def __repr__(self):
        return f"<Stop(id={self.id}, name='{self.name}')>"


class TransportMember(Base):
    """Association table for users (students/staff) and transport routes"""
    __tablename__ = "transport_members"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    stop_id = Column(Integer, ForeignKey("stops.id"), nullable=False)
    
    user = relationship("User")
    route = relationship("Route", back_populates="transport_members")
    stop = relationship("Stop", back_populates="transport_members")

    def __repr__(self):
        return f"<TransportMember(user_id={self.user_id}, route_id={self.route_id})>"
