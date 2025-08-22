"""
API endpoints for managing dynamic forms.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from app.database.session import get_db
from app.models.form import Form, FormField, FormFieldOption
from app.schemas.form import (
    FormCreate,
    FormUpdate,
    Form as FormSchema,
    FormSummary,
    FormSubmissionCreate,
    FormSubmissionResponse,
)
from app.api import deps
from app.models.user import User
from app.models.form_submission import FormSubmission
from app.data.default_forms import get_default_form, get_default_form_fields

router = APIRouter()
logger = logging.getLogger(__name__)


def initialize_default_form(db: Session, entity_type: str) -> Form:
    """Initialize a default form for the given entity type if it doesn't exist"""
    # Check if form already exists
    existing_form = db.query(Form).filter(Form.key == f"{entity_type}_form").first()
    if existing_form:
        return existing_form
    
    # Get default form schema
    default_form_data = get_default_form(entity_type)
    if not default_form_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No default form found for entity type: {entity_type}"
        )
    
    # Create the form
    db_form = Form(
        name=default_form_data["name"],
        key=default_form_data["key"],
        description=default_form_data["description"],
        is_active=True,
    )
    db.add(db_form)
    db.flush()  # Flush to get the form ID

    # Create fields
    for field_data in default_form_data["fields"]:
        db_field = FormField(
            form_id=db_form.id,
            field_type=field_data["field_type"],
            label=field_data["label"],
            field_name=field_data["field_name"],
            placeholder=field_data.get("placeholder", ""),
            is_required=field_data["is_required"],
            is_filterable=field_data["is_filterable"],
            is_visible_in_listing=field_data["is_visible_in_listing"],
            validation_rules=field_data.get("validation_rules", {})
        )
        db.add(db_field)
        db.flush()  # Flush to get the field ID

        # Create options if they exist
        if field_data.get("options"):
            for option_data in field_data["options"]:
                db_option = FormFieldOption(
                    field_id=db_field.id,
                    label=option_data["label"],
                    value=option_data["value"]
                )
                db.add(db_option)

    db.commit()
    db.refresh(db_form)
    return db_form


@router.get(
    "/default/{entity_type}",
    response_model=FormSchema,
    summary="Get or create default form for an entity type"
)
def get_or_create_default_form(entity_type: str, db: Session = Depends(get_db)):
    """
    Get the default form for an entity type. If it doesn't exist, create it.
    """
    try:
        form = initialize_default_form(db, entity_type)
        return form
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while getting/creating default form: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while getting/creating default form.",
        )
    except Exception as e:
        db.rollback()
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.post(
    "/",
    response_model=FormSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new form schema",
)
def create_form(form_in: FormCreate, db: Session = Depends(get_db)):
    """
    Create a new form schema with its fields and options.
    """
    try:
        db_form = Form(
            name=form_in.name,
            key=form_in.key,
            description=form_in.description,
            is_active=form_in.is_active,
        )
        db.add(db_form)
        db.flush()  # Flush to get the form ID

        if form_in.fields:
            for field_in in form_in.fields:
                db_field = FormField(
                    form_id=db_form.id, **field_in.dict(exclude={"options"})
                )
                db.add(db_field)
                db.flush()  # Flush to get the field ID

                if field_in.options:
                    for option_in in field_in.options:
                        db_option = FormFieldOption(
                            field_id=db_field.id, **option_in.dict()
                        )
                        db.add(db_option)

        db.commit()
        db.refresh(db_form)
        return db_form
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating form: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while creating the form.",
        )
    except Exception as e:
        db.rollback()
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.get(
    "/{form_key}",
    response_model=FormSchema,
    summary="Retrieve a form schema by its unique key",
)
def get_form(form_key: str, db: Session = Depends(get_db)):
    """
    Retrieve a single form schema by its key.
    """
    db_form = db.query(Form).filter(Form.key == form_key).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Form not found"
        )
    return db_form


@router.put(
    "/{form_key}", response_model=FormSchema, summary="Update an existing form schema"
)
def update_form(form_key: str, form_in: FormUpdate, db: Session = Depends(get_db)):
    """
    Update an existing form schema, including its fields and options.
    This endpoint handles partial updates intelligently without deleting and recreating fields.
    """
    try:
        db_form = db.query(Form).filter(Form.key == form_key).first()
        if not db_form:
            logger.warning(f"Form with key '{form_key}' not found for update.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Form not found"
            )

        # Update form attributes
        update_data = form_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field != "fields":
                setattr(db_form, field, value)

        if "fields" in update_data:
            # Create a map of existing fields by their ID for quick lookup
            existing_fields = {str(field.id): field for field in db_form.fields}

            for field_data in update_data["fields"]:
                field_id = str(field_data.get("id"))
                if field_id in existing_fields:
                    # Update existing field
                    db_field = existing_fields.pop(field_id)
                    # Only update fields that exist in the FormField model
                    valid_fields = {
                        'label', 'field_name', 'field_type', 'placeholder', 
                        'default_value', 'is_required', 'is_filterable', 
                        'is_visible_in_listing', 'validation_rules', 'order'
                    }
                    for key, value in field_data.items():
                        if key in valid_fields:
                            setattr(db_field, key, value)

                    # Update options
                    if "options" in field_data:
                        existing_options = {
                            str(opt.id): opt for opt in db_field.options
                        }
                        for opt_data in field_data["options"]:
                            opt_id = str(opt_data.get("id"))
                            if opt_id in existing_options:
                                db_option = existing_options.pop(opt_id)
                                # Only update fields that exist in the FormFieldOption model
                                valid_option_fields = {'label', 'value', 'order'}
                                for key, value in opt_data.items():
                                    if key in valid_option_fields:
                                        setattr(db_option, key, value)
                            else:
                                option_kwargs = {
                                    'field_id': db_field.id,
                                    'label': opt_data.get('label', ''),
                                    'value': opt_data.get('value', ''),
                                    'order': opt_data.get('order', 0)
                                }
                                new_option = FormFieldOption(**option_kwargs)
                                db.add(new_option)
                        # Delete options that were not in the request
                        for opt in existing_options.values():
                            db.delete(opt)
                else:
                    # Create new field
                    # Extract only the fields that exist in the FormField model
                    field_kwargs = {
                        'form_id': db_form.id,
                        'label': field_data.get('label', ''),
                        'field_name': field_data.get('field_name', ''),
                        'field_type': field_data.get('field_type'),
                        'placeholder': field_data.get('placeholder'),
                        'default_value': field_data.get('default_value'),
                        'is_required': field_data.get('is_required', False),
                        'is_filterable': field_data.get('is_filterable', False),
                        'is_visible_in_listing': field_data.get('is_visible_in_listing', False),
                        'validation_rules': field_data.get('validation_rules'),
                        'order': field_data.get('order', 0)
                    }
                    new_field = FormField(**field_kwargs)
                    db.add(new_field)
                    db.flush()  # Flush to get the field ID
                    
                    # Add options if they exist
                    if 'options' in field_data and field_data['options']:
                        for opt_data in field_data['options']:
                            option_kwargs = {
                                'field_id': new_field.id,
                                'label': opt_data.get('label', ''),
                                'value': opt_data.get('value', ''),
                                'order': opt_data.get('order', 0)
                            }
                            new_option = FormFieldOption(**option_kwargs)
                            db.add(new_option)

            # Delete fields that were not in the request
            for field in existing_fields.values():
                db.delete(field)

        db.commit()
        db.refresh(db_form)
        return db_form
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while updating form '{form_key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while updating the form.",
        )
    except Exception as e:
        db.rollback()
        logger.error(f"An unexpected error occurred while updating form '{form_key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.delete(
    "/{form_key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a form schema",
)
def delete_form(form_key: str, db: Session = Depends(get_db)):
    """
    Delete a form schema by its key.
    """
    try:
        db_form = db.query(Form).filter(Form.key == form_key).first()
        if not db_form:
            logger.warning(f"Form with key '{form_key}' not found for deletion.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Form not found"
            )
        db.delete(db_form)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while deleting form '{form_key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while deleting the form.",
        )
    except Exception as e:
        db.rollback()
        logger.error(f"An unexpected error occurred while deleting form '{form_key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.get(
    "/", response_model=List[FormSummary], summary="List all available form schemas"
)
def list_forms(db: Session = Depends(get_db)):
    """
    Retrieve a list of all form schemas.
    """
    try:
        return db.query(Form).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error while listing forms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while retrieving forms.",
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred while listing forms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.get(
    "/{form_key}/render",
    response_model=FormSchema,
    summary="Retrieve a form schema for rendering",
)
def get_form_for_rendering(form_key: str, db: Session = Depends(get_db)):
    """
    Retrieve a single form schema by its key for rendering.
    """
    db_form = db.query(Form).filter(Form.key == form_key, Form.is_active == True).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Form not found"
        )
    return db_form

@router.post(
    "/{form_key}/submit",
    response_model=FormSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit data for a form",
)
def submit_form(
    form_key: str,
    submission_in: FormSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Submit data for a specific form.
    """
    db_form = db.query(Form).filter(Form.key == form_key, Form.is_active == True).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Form not found"
        )

    db_submission = FormSubmission(
        form_id=db_form.id,
        user_id=current_user.id,
        data=submission_in.data,
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission