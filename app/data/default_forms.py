"""
Default form schemas for different entities
"""

from typing import Dict, Any
from app.models.form import FieldType

# Default student form based on StudentBase schema
DEFAULT_STUDENT_FORM = {
    "name": "Student Registration Form",
    "key": "student_form",
    "description": "Default form for student registration based on StudentBase schema",
    "entityType": "student",
    "fields": [
        {
            "id": "email",
            "field_type": FieldType.EMAIL,
            "label": "Email Address",
            "field_name": "email",
            "placeholder": "Enter email address",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True,
                "type": "email"
            }
        },
        {
            "id": "password",
            "field_type": FieldType.PASSWORD,
            "label": "Password",
            "field_name": "password",
            "placeholder": "Enter password",
            "is_required": True,
            "is_filterable": False,
            "is_visible_in_listing": False,
            "validation_rules": {
                "required": True,
                "minLength": 6
            }
        },
        {
            "id": "first_name",
            "field_type": FieldType.TEXT,
            "label": "First Name",
            "field_name": "first_name",
            "placeholder": "Enter first name",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True,
                "minLength": 1
            }
        },
        {
            "id": "last_name",
            "field_type": FieldType.TEXT,
            "label": "Last Name",
            "field_name": "last_name",
            "placeholder": "Enter last name",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True,
                "minLength": 1
            }
        },
        {
            "id": "student_id",
            "field_type": FieldType.TEXT,
            "label": "Student ID",
            "field_name": "student_id",
            "placeholder": "Enter student ID",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True,
                "minLength": 1
            }
        },
        {
            "id": "admission_date",
            "field_type": FieldType.DATE,
            "label": "Admission Date",
            "field_name": "admission_date",
            "placeholder": "Select admission date",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            }
        },
        {
            "id": "academic_year",
            "field_type": FieldType.TEXT,
            "label": "Academic Year",
            "field_name": "academic_year",
            "placeholder": "e.g., 2023-2024",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True,
                "pattern": r"^\d{4}-\d{4}$"
            }
        },
        {
            "id": "phone",
            "field_type": FieldType.PHONE,
            "label": "Phone Number",
            "field_name": "phone",
            "placeholder": "Enter phone number",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False,
                "pattern": r"^[0-9+\-\s()]+$"
            }
        },
        {
            "id": "roll_number",
            "field_type": FieldType.TEXT,
            "label": "Roll Number",
            "field_name": "roll_number",
            "placeholder": "Enter roll number",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False
            }
        },
        {
            "id": "section",
            "field_type": FieldType.TEXT,
            "label": "Section",
            "field_name": "section",
            "placeholder": "Enter section (e.g., A, B, C)",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False,
                "maxLength": 10
            }
        },
        {
            "id": "blood_group",
            "field_type": FieldType.SELECT,
            "label": "Blood Group",
            "field_name": "blood_group",
            "placeholder": "Select blood group",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False
            },
            "options": [
                {"id": "1", "label": "A+", "value": "A+"},
                {"id": "2", "label": "A-", "value": "A-"},
                {"id": "3", "label": "B+", "value": "B+"},
                {"id": "4", "label": "B-", "value": "B-"},
                {"id": "5", "label": "AB+", "value": "AB+"},
                {"id": "6", "label": "AB-", "value": "AB-"},
                {"id": "7", "label": "O+", "value": "O+"},
                {"id": "8", "label": "O-", "value": "O-"}
            ]
        },
        {
            "id": "transportation_mode",
            "field_type": FieldType.SELECT,
            "label": "Transportation Mode",
            "field_name": "transportation_mode",
            "placeholder": "Select transportation mode",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False
            },
            "options": [
                {"id": "1", "label": "School Bus", "value": "school_bus"},
                {"id": "2", "label": "Private Vehicle", "value": "private_vehicle"},
                {"id": "3", "label": "Public Transport", "value": "public_transport"},
                {"id": "4", "label": "Walking", "value": "walking"},
                {"id": "5", "label": "Other", "value": "other"}
            ]
        },
        {
            "id": "is_hosteller",
            "field_type": FieldType.CHECKBOX,
            "label": "Is Hosteller",
            "field_name": "is_hosteller",
            "placeholder": "",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False
            }
        }
    ]
}

# Dictionary mapping entity types to their default forms
DEFAULT_FORMS: Dict[str, Dict[str, Any]] = {
    "student": DEFAULT_STUDENT_FORM,
    # Add more default forms for other entities here
}

def get_default_form(entity_type: str) -> Dict[str, Any]:
    """Get the default form schema for a given entity type"""
    return DEFAULT_FORMS.get(entity_type, {})

def get_default_form_fields(entity_type: str) -> list:
    """Get the default form fields for a given entity type"""
    default_form = get_default_form(entity_type)
    return default_form.get("fields", [])
