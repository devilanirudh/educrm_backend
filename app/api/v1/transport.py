"""transport API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.models import transport as models
from app.schemas import transport as schemas

router = APIRouter()

# Vehicle Endpoints
@router.post("/vehicles/", response_model=schemas.Vehicle)
def create_vehicle(vehicle: schemas.VehicleCreate, db: Session = Depends(deps.get_db)):
    db_vehicle = models.Vehicle(**vehicle.dict())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@router.get("/vehicles/", response_model=List[schemas.Vehicle])
def read_vehicles(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    vehicles = db.query(models.Vehicle).offset(skip).limit(limit).all()
    return vehicles

@router.get("/vehicles/{vehicle_id}", response_model=schemas.Vehicle)
def read_vehicle(vehicle_id: int, db: Session = Depends(deps.get_db)):
    db_vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return db_vehicle

@router.put("/vehicles/{vehicle_id}", response_model=schemas.Vehicle)
def update_vehicle(vehicle_id: int, vehicle: schemas.VehicleUpdate, db: Session = Depends(deps.get_db)):
    db_vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    for var, value in vars(vehicle).items():
        setattr(db_vehicle, var, value) if value else None
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@router.delete("/vehicles/{vehicle_id}", response_model=schemas.Vehicle)
def delete_vehicle(vehicle_id: int, db: Session = Depends(deps.get_db)):
    db_vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    db.delete(db_vehicle)
    db.commit()
    return db_vehicle

# Route Endpoints
@router.post("/routes/", response_model=schemas.Route)
def create_route(route: schemas.RouteCreate, db: Session = Depends(deps.get_db)):
    db_route = models.Route(**route.dict())
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route

@router.get("/routes/", response_model=List[schemas.Route])
def read_routes(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    routes = db.query(models.Route).offset(skip).limit(limit).all()
    return routes

@router.get("/routes/{route_id}", response_model=schemas.Route)
def read_route(route_id: int, db: Session = Depends(deps.get_db)):
    db_route = db.query(models.Route).filter(models.Route.id == route_id).first()
    if db_route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    return db_route

@router.put("/routes/{route_id}", response_model=schemas.Route)
def update_route(route_id: int, route: schemas.RouteUpdate, db: Session = Depends(deps.get_db)):
    db_route = db.query(models.Route).filter(models.Route.id == route_id).first()
    if db_route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    for var, value in vars(route).items():
        setattr(db_route, var, value) if value else None
    db.commit()
    db.refresh(db_route)
    return db_route

@router.delete("/routes/{route_id}", response_model=schemas.Route)
def delete_route(route_id: int, db: Session = Depends(deps.get_db)):
    db_route = db.query(models.Route).filter(models.Route.id == route_id).first()
    if db_route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    db.delete(db_route)
    db.commit()
    return db_route

# Stop Endpoints
@router.post("/stops/", response_model=schemas.Stop)
def create_stop(stop: schemas.StopCreate, db: Session = Depends(deps.get_db)):
    db_stop = models.Stop(**stop.dict())
    db.add(db_stop)
    db.commit()
    db.refresh(db_stop)
    return db_stop

@router.get("/stops/", response_model=List[schemas.Stop])
def read_stops(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    stops = db.query(models.Stop).offset(skip).limit(limit).all()
    return stops

@router.get("/stops/{stop_id}", response_model=schemas.Stop)
def read_stop(stop_id: int, db: Session = Depends(deps.get_db)):
    db_stop = db.query(models.Stop).filter(models.Stop.id == stop_id).first()
    if db_stop is None:
        raise HTTPException(status_code=404, detail="Stop not found")
    return db_stop

@router.put("/stops/{stop_id}", response_model=schemas.Stop)
def update_stop(stop_id: int, stop: schemas.StopUpdate, db: Session = Depends(deps.get_db)):
    db_stop = db.query(models.Stop).filter(models.Stop.id == stop_id).first()
    if db_stop is None:
        raise HTTPException(status_code=404, detail="Stop not found")
    for var, value in vars(stop).items():
        setattr(db_stop, var, value) if value else None
    db.commit()
    db.refresh(db_stop)
    return db_stop

@router.delete("/stops/{stop_id}", response_model=schemas.Stop)
def delete_stop(stop_id: int, db: Session = Depends(deps.get_db)):
    db_stop = db.query(models.Stop).filter(models.Stop.id == stop_id).first()
    if db_stop is None:
        raise HTTPException(status_code=404, detail="Stop not found")
    db.delete(db_stop)
    db.commit()
    return db_stop

# TransportMember Endpoints
@router.post("/transport_members/", response_model=schemas.TransportMember)
def create_transport_member(transport_member: schemas.TransportMemberCreate, db: Session = Depends(deps.get_db)):
    db_transport_member = models.TransportMember(**transport_member.dict())
    db.add(db_transport_member)
    db.commit()
    db.refresh(db_transport_member)
    return db_transport_member

@router.get("/transport_members/", response_model=List[schemas.TransportMember])
def read_transport_members(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    transport_members = db.query(models.TransportMember).offset(skip).limit(limit).all()
    return transport_members

@router.get("/transport_members/{transport_member_id}", response_model=schemas.TransportMember)
def read_transport_member(transport_member_id: int, db: Session = Depends(deps.get_db)):
    db_transport_member = db.query(models.TransportMember).filter(models.TransportMember.id == transport_member_id).first()
    if db_transport_member is None:
        raise HTTPException(status_code=404, detail="Transport member not found")
    return db_transport_member

@router.put("/transport_members/{transport_member_id}", response_model=schemas.TransportMember)
def update_transport_member(transport_member_id: int, transport_member: schemas.TransportMemberUpdate, db: Session = Depends(deps.get_db)):
    db_transport_member = db.query(models.TransportMember).filter(models.TransportMember.id == transport_member_id).first()
    if db_transport_member is None:
        raise HTTPException(status_code=404, detail="Transport member not found")
    for var, value in vars(transport_member).items():
        setattr(db_transport_member, var, value) if value else None
    db.commit()
    db.refresh(db_transport_member)
    return db_transport_member

@router.delete("/transport_members/{transport_member_id}", response_model=schemas.TransportMember)
def delete_transport_member(transport_member_id: int, db: Session = Depends(deps.get_db)):
    db_transport_member = db.query(models.TransportMember).filter(models.TransportMember.id == transport_member_id).first()
    if db_transport_member is None:
        raise HTTPException(status_code=404, detail="Transport member not found")
    db.delete(db_transport_member)
    db.commit()
    return db_transport_member
