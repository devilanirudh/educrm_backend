"""
Pydantic schemas for Transport module
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time

# Stop Schemas
class StopBase(BaseModel):
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    arrival_time_am: Optional[time] = None
    departure_time_am: Optional[time] = None
    arrival_time_pm: Optional[time] = None
    departure_time_pm: Optional[time] = None
    route_id: int

class StopCreate(StopBase):
    pass

class StopUpdate(StopBase):
    pass

class Stop(StopBase):
    id: int

    class Config:
        orm_mode = True

# Route Schemas
class RouteBase(BaseModel):
    name: str
    description: Optional[str] = None

class RouteCreate(RouteBase):
    pass

class RouteUpdate(RouteBase):
    pass

class Route(RouteBase):
    id: int
    stops: List[Stop] = []

    class Config:
        orm_mode = True

# Vehicle Schemas
class VehicleBase(BaseModel):
    registration_number: str
    capacity: int
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    insurance_expiry: Optional[date] = None
    is_active: bool = True
    route_id: Optional[int] = None

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(VehicleBase):
    pass

class Vehicle(VehicleBase):
    id: int

    class Config:
        orm_mode = True

# TransportMember Schemas
class TransportMemberBase(BaseModel):
    user_id: int
    route_id: int
    stop_id: int

class TransportMemberCreate(TransportMemberBase):
    pass

class TransportMemberUpdate(TransportMemberBase):
    pass

class TransportMember(TransportMemberBase):
    id: int

    class Config:
        orm_mode = True