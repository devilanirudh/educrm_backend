"""exams API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.exam import ExamTerm, DateSheet, DateSheetEntry
from app.schemas.exam import ExamTermCreate, ExamTermResponse, ExamTermUpdate, DateSheetCreate, DateSheetResponse, DateSheetUpdate
from app.models.user import User
from typing import List

router = APIRouter()

@router.post("/terms", response_model=ExamTermResponse)
def create_exam_term(
    *,
    db: Session = Depends(deps.get_db),
    term_in: ExamTermCreate,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Create new exam term.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db_term = ExamTerm(**term_in.dict())
    db.add(db_term)
    db.commit()
    db.refresh(db_term)
    return db_term

@router.get("/terms", response_model=List[ExamTermResponse])
def read_exam_terms(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Retrieve exam terms.
    """
    terms = db.query(ExamTerm).offset(skip).limit(limit).all()
    return terms

@router.put("/terms/{term_id}", response_model=ExamTermResponse)
def update_exam_term(
    *,
    db: Session = Depends(deps.get_db),
    term_id: int,
    term_in: ExamTermUpdate,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Update an exam term.
    """
    term = db.query(ExamTerm).filter(ExamTerm.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Exam term not found")
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    update_data = term_in.dict(exclude_unset=True)
    for field in update_data:
        setattr(term, field, update_data[field])
    
    db.add(term)
    db.commit()
    db.refresh(term)
    return term

@router.delete("/terms/{term_id}", status_code=204)
def delete_exam_term(
    *,
    db: Session = Depends(deps.get_db),
    term_id: int,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Delete an exam term.
    """
    term = db.query(ExamTerm).filter(ExamTerm.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Exam term not found")
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db.delete(term)
    db.commit()
    return {"ok": True}

@router.post("/datesheets", response_model=DateSheetResponse)
def create_datesheet(
    *,
    db: Session = Depends(deps.get_db),
    datesheet_in: DateSheetCreate,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Create new datesheet.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db_datesheet = DateSheet(
        class_id=datesheet_in.class_id,
        term_id=datesheet_in.term_id,
        status=datesheet_in.status,
    )
    db.add(db_datesheet)
    db.commit()
    db.refresh(db_datesheet)

    for entry in datesheet_in.entries:
        db_entry = DateSheetEntry(**entry.dict(), datesheet_id=db_datesheet.id)
        db.add(db_entry)
    
    db.commit()
    db.refresh(db_datesheet)
    return db_datesheet

@router.get("/datesheets/{class_id}/{term_id}", response_model=DateSheetResponse)
def read_datesheet(
    *,
    db: Session = Depends(deps.get_db),
    class_id: int,
    term_id: int,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get datesheet by class and term.
    """
    datesheet = db.query(DateSheet).filter(DateSheet.class_id == class_id, DateSheet.term_id == term_id).first()
    if not datesheet:
        raise HTTPException(status_code=404, detail="Datesheet not found")
    return datesheet

@router.put("/datesheets/{datesheet_id}", response_model=DateSheetResponse)
def update_datesheet(
    *,
    db: Session = Depends(deps.get_db),
    datesheet_id: int,
    datesheet_in: DateSheetUpdate,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Update a datesheet.
    """
    datesheet = db.query(DateSheet).filter(DateSheet.id == datesheet_id).first()
    if not datesheet:
        raise HTTPException(status_code=404, detail="Datesheet not found")
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    update_data = datesheet_in.dict(exclude_unset=True)
    if "status" in update_data:
        datesheet.status = update_data["status"]
    
    if "entries" in update_data:
        # Clear existing entries
        for entry in datesheet.entries:
            db.delete(entry)
        db.commit()

        # Add new entries
        for entry_data in update_data["entries"]:
            db_entry = DateSheetEntry(**entry_data, datesheet_id=datesheet.id)
            db.add(db_entry)
        db.commit()

    db.add(datesheet)
    db.commit()
    db.refresh(datesheet)
    return datesheet

@router.post("/datesheets/{datesheet_id}/publish", response_model=DateSheetResponse)
def publish_datesheet(
    *,
    db: Session = Depends(deps.get_db),
    datesheet_id: int,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Publish a datesheet and notify students and teachers.
    """
    datesheet = db.query(DateSheet).filter(DateSheet.id == datesheet_id).first()
    if not datesheet:
        raise HTTPException(status_code=404, detail="Datesheet not found")

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    datesheet.status = "published"
    db.add(datesheet)
    db.commit()
    db.refresh(datesheet)

    # TODO: Implement notification logic for students and teachers

    return datesheet
