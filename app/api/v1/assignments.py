"""assignments API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.academic import Assignment
from app.schemas.assignment import AssignmentCreate, AssignmentResponse, AssignmentUpdate, AssignmentSubmissionResponse, AssignmentSubmissionCreate
from app.models.user import User
from typing import List, Optional
from datetime import date

router = APIRouter()

@router.post("", response_model=AssignmentResponse)
def create_assignment(
    *,
    db: Session = Depends(deps.get_db),
    assignment_in: AssignmentCreate,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Create new assignment.
    """
    if not current_user.role in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db_assignment = Assignment(**assignment_in.dict())
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

@router.get("", response_model=List[AssignmentResponse])
def read_assignments(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    class_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    due_date_start: Optional[date] = None,
    due_date_end: Optional[date] = None,
    status: Optional[str] = None,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Retrieve assignments.
    """
    query = db.query(Assignment)
    if class_id:
        query = query.filter(Assignment.class_id == class_id)
    if subject_id:
        query = query.filter(Assignment.subject_id == subject_id)
    if due_date_start:
        query = query.filter(Assignment.due_date >= due_date_start)
    if due_date_end:
        query = query.filter(Assignment.due_date <= due_date_end)
    if status:
        # This assumes a 'status' field exists on the Assignment model.
        # If not, this part needs adjustment.
        query = query.filter(Assignment.status == status)
    
    assignments = query.offset(skip).limit(limit).all()
    return assignments

@router.get("/{assignment_id}", response_model=AssignmentResponse)
def read_assignment(
    *,
    db: Session = Depends(deps.get_db),
    assignment_id: int,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get assignment by ID.
    """
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment

@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    *,
    db: Session = Depends(deps.get_db),
    assignment_id: int,
    assignment_in: AssignmentUpdate,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Update an assignment.
    """
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if not current_user.role in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    update_data = assignment_in.dict(exclude_unset=True)
    for field in update_data:
        setattr(assignment, field, update_data[field])
    
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment

@router.delete("/{assignment_id}", status_code=204)
def delete_assignment(
    *,
    db: Session = Depends(deps.get_db),
    assignment_id: int,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Delete an assignment.
    """
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if not current_user.role in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db.delete(assignment)
    db.commit()
    return {"ok": True}

@router.post("/{assignment_id}/submit", response_model=AssignmentSubmissionResponse)
def submit_assignment(
    *,
    db: Session = Depends(deps.get_db),
    assignment_id: int,
    submission_in: AssignmentSubmissionCreate,
    current_user: User = Depends(deps.get_current_student_user),
):
    """
    Submit an assignment.
    """
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # TODO: Check if student is in the class for this assignment
    # TODO: Check for late submissions and apply penalties if necessary

    db_submission = AssignmentSubmission(**submission_in.dict(), student_id=current_user.id)
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission
