"""
API endpoints for managing dynamic forms.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from app.database.session import get_db
from app.models.form_submission import FormSubmission
from app.schemas.form_submission import (
    FormSubmissionCreate,
    FormSubmission as FormSubmissionSchema,
)
from app.api import deps

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/",
    response_model=FormSubmissionSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new form submission",
)
def create_form_submission(
    form_submission_in: FormSubmissionCreate, db: Session = Depends(get_db)
):
    """
    Create a new form submission.
    """
    try:
        db_form_submission = FormSubmission(**form_submission_in.dict())
        db.add(db_form_submission)
        db.commit()
        db.refresh(db_form_submission)
        return db_form_submission
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating form submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while creating the form submission.",
        )
    except Exception as e:
        db.rollback()
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.get(
    "/{form_id}",
    response_model=List[FormSubmissionSchema],
    summary="Retrieve all form submissions for a form",
)
def get_form_submissions(form_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all form submissions for a form.
    """
    try:
        return (
            db.query(FormSubmission)
            .filter(FormSubmission.form_id == form_id)
            .all()
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error while listing form submissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while retrieving form submissions.",
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred while listing form submissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )