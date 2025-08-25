#!/usr/bin/env python3
"""
Script to update the assignment form schema in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.models.form import Form, FormField, FieldType
from app.data.default_forms import DEFAULT_ASSIGNMENT_FORM

def update_assignment_form():
    db = SessionLocal()
    
    try:
        # Find existing assignment form
        assignment_form = db.query(Form).filter(Form.key == "assignment_form").first()
        
        if assignment_form:
            print("Updating existing assignment form...")
            
            # Update the form fields
            for field in assignment_form.fields:
                if field.field_name == 'teacher_id':
                    field.field_type = FieldType.SELECT
                    field.label = "Teacher"
                    field.placeholder = "Select teacher"
                    print(f"Updated {field.field_name} to SELECT type")
                elif field.field_name == 'class_id':
                    field.field_type = FieldType.SELECT
                    field.label = "Class"
                    field.placeholder = "Select class"
                    print(f"Updated {field.field_name} to SELECT type")
                elif field.field_name == 'subject_id':
                    field.field_type = FieldType.SELECT
                    field.label = "Subject"
                    field.placeholder = "Select subject"
                    print(f"Updated {field.field_name} to SELECT type")
            
            db.commit()
            print("Assignment form updated successfully!")
            
        else:
            print("Assignment form not found. Creating new one...")
            # Create new form from default
            from app.services.form_service import create_form_from_schema
            create_form_from_schema(DEFAULT_ASSIGNMENT_FORM, db)
            print("Assignment form created successfully!")
            
    except Exception as e:
        print(f"Error updating assignment form: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_assignment_form()
