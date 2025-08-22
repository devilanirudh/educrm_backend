"""
API endpoints for the Report Card Builder feature.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.models import user as user_model
from app.models import report_card as report_card_model
from app.schemas import report_card as report_card_schema

router = APIRouter()


@router.post("/templates", response_model=report_card_schema.ReportCardTemplate)
def create_report_card_template(
    *,
    db: Session = Depends(deps.get_db),
    current_user: user_model.User = Depends(deps.get_current_active_user),
    template_in: report_card_schema.ReportCardTemplateCreate,
):
    """
    Create a new report card template.
    """
    db_template = report_card_model.ReportCardTemplate(**template_in.dict())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


@router.get("/templates", response_model=List[report_card_schema.ReportCardTemplate])
def read_report_card_templates(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve all report card templates.
    """
    templates = db.query(report_card_model.ReportCardTemplate).offset(skip).limit(limit).all()
    return templates


@router.post("/publish")
def publish_report_card(
    *,
    db: Session = Depends(deps.get_db),
    current_user: user_model.User = Depends(deps.get_current_active_user),
    publish_in: report_card_schema.ReportCardPublish,
):
    """
    Publish a report card template to teachers for a specific class and term.
    """
    # This is a placeholder implementation.
    # In a real application, you would create report card entries for each student.
    return {"message": "Report card published successfully."}


@router.post("/submit")
def submit_report_card(
    *,
    db: Session = Depends(deps.get_db),
    current_user: user_model.User = Depends(deps.get_current_active_user),
    submit_in: report_card_schema.ReportCardSubmit,
):
    """
    Allow teachers to submit filled report card data.
    """
    report_card = (
        db.query(report_card_model.ReportCard)
        .filter(report_card_model.ReportCard.id == submit_in.report_card_id)
        .first()
    )
    if not report_card:
        raise HTTPException(status_code=404, detail="Report card not found")

    report_card.data = submit_in.data
    report_card.status = "submitted"
    report_card.submitted_by_id = current_user.id
    db.commit()
    return {"message": "Report card submitted successfully."}


@router.post("/generate-pdf")
def generate_report_card_pdf(
    *,
    db: Session = Depends(deps.get_db),
    current_user: user_model.User = Depends(deps.get_current_active_user),
    generate_in: report_card_schema.ReportCardGeneratePDF,
):
    """
    Generate a PDF for a student's report card.
    """
    # This is a placeholder implementation.
    # In a real application, you would generate a PDF using a library like WeasyPrint or ReportLab.
    return {"message": "PDF generation initiated."}