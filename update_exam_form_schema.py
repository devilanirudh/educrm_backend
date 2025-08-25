#!/usr/bin/env python3
"""
Script to update the exam form schema in the database
Adds teacher_id, class_id, subject_id dropdowns and file upload fields
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.models.form import Form, FormField, FormFieldOption, FieldType
from app.data.default_forms import DEFAULT_EXAM_FORM
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_exam_form_schema():
    """Update the exam form schema in the database"""
    db = SessionLocal()
    
    try:
        # Get the existing exam form
        exam_form = db.query(Form).filter(Form.key == "exam_form").first()
        
        if not exam_form:
            logger.info("Creating new exam form...")
            # Create new exam form
            exam_form = Form(
                name=DEFAULT_EXAM_FORM["name"],
                key=DEFAULT_EXAM_FORM["key"],
                description=DEFAULT_EXAM_FORM["description"],
                entity_type=DEFAULT_EXAM_FORM["entityType"],
                is_active=True
            )
            db.add(exam_form)
            db.flush()  # Get the ID
            
            # Create all fields
            for field_data in DEFAULT_EXAM_FORM["fields"]:
                field = FormField(
                    form_id=exam_form.id,
                    field_type=field_data["field_type"],
                    label=field_data["label"],
                    field_name=field_data["field_name"],
                    placeholder=field_data["placeholder"],
                    is_required=field_data["is_required"],
                    is_filterable=field_data["is_filterable"],
                    is_visible_in_listing=field_data["is_visible_in_listing"],
                    validation_rules=field_data["validation_rules"]
                )
                db.add(field)
                db.flush()  # Get the field ID
                
                # Add options for select fields
                if field_data.get("options"):
                    for option_data in field_data["options"]:
                        option = FormFieldOption(
                            field_id=field.id,
                            label=option_data["label"],
                            value=option_data["value"],
                            order=option_data.get("order", 0)
                        )
                        db.add(option)
            
            logger.info("✅ New exam form created successfully!")
            
        else:
            logger.info("Updating existing exam form...")
            
            # Delete existing fields and options
            existing_fields = db.query(FormField).filter(FormField.form_id == exam_form.id).all()
            for field in existing_fields:
                # Delete options first
                db.query(FormFieldOption).filter(FormFieldOption.field_id == field.id).delete()
                # Delete field
                db.delete(field)
            
            # Update form metadata
            exam_form.name = DEFAULT_EXAM_FORM["name"]
            exam_form.description = DEFAULT_EXAM_FORM["description"]
            exam_form.entity_type = DEFAULT_EXAM_FORM["entityType"]
            
            # Create new fields
            for field_data in DEFAULT_EXAM_FORM["fields"]:
                field = FormField(
                    form_id=exam_form.id,
                    field_type=field_data["field_type"],
                    label=field_data["label"],
                    field_name=field_data["field_name"],
                    placeholder=field_data["placeholder"],
                    is_required=field_data["is_required"],
                    is_filterable=field_data["is_filterable"],
                    is_visible_in_listing=field_data["is_visible_in_listing"],
                    validation_rules=field_data["validation_rules"]
                )
                db.add(field)
                db.flush()  # Get the field ID
                
                # Add options for select fields
                if field_data.get("options"):
                    for option_data in field_data["options"]:
                        option = FormFieldOption(
                            field_id=field.id,
                            label=option_data["label"],
                            value=option_data["value"],
                            order=option_data.get("order", 0)
                        )
                        db.add(option)
            
            logger.info("✅ Exam form updated successfully!")
        
        # Commit changes
        db.commit()
        
        # Log the updated fields
        updated_fields = db.query(FormField).filter(FormField.form_id == exam_form.id).all()
        logger.info(f"📋 Exam form now has {len(updated_fields)} fields:")
        for field in updated_fields:
            logger.info(f"  - {field.field_name}: {field.field_type} ({'Required' if field.is_required else 'Optional'})")
        
    except Exception as e:
        logger.error(f"❌ Error updating exam form: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("🔄 Starting exam form schema update...")
    update_exam_form_schema()
    logger.info("✅ Exam form schema update completed!")
