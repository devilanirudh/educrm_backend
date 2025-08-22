"""
API endpoints for managing events.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.models.event import Event
from app.schemas.event import EventCreate, EventUpdate, EventResponse

router = APIRouter()

@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event_in: EventCreate, db: Session = Depends(get_db)):
    """
    Create a new event.
    """
    db_event = Event(**event_in.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.get("/", response_model=List[EventResponse])
def get_events(db: Session = Depends(get_db)):
    """
    Retrieve all events.
    """
    return db.query(Event).all()

@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single event by its ID.
    """
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return db_event

@router.put("/{event_id}", response_model=EventResponse)
def update_event(event_id: int, event_in: EventUpdate, db: Session = Depends(get_db)):
    """
    Update an existing event.
    """
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    for field, value in event_in.dict(exclude_unset=True).items():
        setattr(db_event, field, value)

    db.commit()
    db.refresh(db_event)
    return db_event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    """
    Delete an event by its ID.
    """
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    db.delete(db_event)
    db.commit()
    return
