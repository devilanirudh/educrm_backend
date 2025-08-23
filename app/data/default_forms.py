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

# Default teacher form based on Teacher schema
DEFAULT_TEACHER_FORM = {
    "name": "Teacher Registration Form",
    "key": "teacher_form",
    "description": "Default form for teacher registration based on Teacher schema",
    "entityType": "teacher",
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
            "id": "employee_id",
            "field_type": FieldType.TEXT,
            "label": "Employee ID",
            "field_name": "employee_id",
            "placeholder": "Enter employee ID",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True,
                "minLength": 1
            }
        },
        {
            "id": "hire_date",
            "field_type": FieldType.DATE,
            "label": "Hire Date",
            "field_name": "hire_date",
            "placeholder": "Select hire date",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
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
            "id": "qualifications",
            "field_type": FieldType.TEXTAREA,
            "label": "Qualifications",
            "field_name": "qualifications",
            "placeholder": "Enter qualifications",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": False,
            "validation_rules": {
                "required": False
            }
        },
        {
            "id": "experience",
            "field_type": FieldType.NUMBER,
            "label": "Years of Experience",
            "field_name": "experience",
            "placeholder": "Enter years of experience",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False,
                "min": 0,
                "max": 50
            }
        },
        {
            "id": "specialization",
            "field_type": FieldType.TEXT,
            "label": "Specialization",
            "field_name": "specialization",
            "placeholder": "Enter specialization",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False
            }
        },
        {
            "id": "employment_type",
            "field_type": FieldType.SELECT,
            "label": "Employment Type",
            "field_name": "employment_type",
            "placeholder": "Select employment type",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            },
            "options": [
                {"id": "1", "label": "Full Time", "value": "full_time"},
                {"id": "2", "label": "Part Time", "value": "part_time"},
                {"id": "3", "label": "Contract", "value": "contract"},
                {"id": "4", "label": "Visiting", "value": "visiting"}
            ]
        },
        {
            "id": "department",
            "field_type": FieldType.SELECT,
            "label": "Department",
            "field_name": "department",
            "placeholder": "Select department",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False
            },
            "options": [
                {"id": "1", "label": "Mathematics", "value": "mathematics"},
                {"id": "2", "label": "English", "value": "english"},
                {"id": "3", "label": "Science", "value": "science"},
                {"id": "4", "label": "History", "value": "history"},
                {"id": "5", "label": "Geography", "value": "geography"},
                {"id": "6", "label": "Computer Science", "value": "computer_science"},
                {"id": "7", "label": "Physical Education", "value": "physical_education"},
                {"id": "8", "label": "Arts", "value": "arts"},
                {"id": "9", "label": "Music", "value": "music"},
                {"id": "10", "label": "Administration", "value": "administration"}
            ]
        },
        {
            "id": "salary",
            "field_type": FieldType.NUMBER,
            "label": "Salary",
            "field_name": "salary",
            "placeholder": "Enter salary",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": False,
            "validation_rules": {
                "required": False,
                "min": 0
            }
        },
        {
            "id": "designation",
            "field_type": FieldType.TEXT,
            "label": "Designation",
            "field_name": "designation",
            "placeholder": "Enter designation",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False
            }
        },
        {
            "id": "teaching_philosophy",
            "field_type": FieldType.TEXTAREA,
            "label": "Teaching Philosophy",
            "field_name": "teaching_philosophy",
            "placeholder": "Enter teaching philosophy",
            "is_required": False,
            "is_filterable": False,
            "is_visible_in_listing": False,
            "validation_rules": {
                "required": False
            }
        }
    ]
}

# Default class form based on Class schema
DEFAULT_CLASS_FORM = {
    "name": "Class Registration Form",
    "key": "class_form",
    "description": "Default form for class registration and management",
    "entityType": "class",
    "fields": [
        {
            "id": "name",
            "field_type": FieldType.TEXT,
            "label": "Class Name",
            "field_name": "name",
            "placeholder": "Enter class name",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True,
                "minLength": 1,
                "maxLength": 50
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
            "id": "stream",
            "field_type": FieldType.SELECT,
            "label": "Stream",
            "field_name": "stream",
            "placeholder": "Select stream",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False
            },
            "options": [
                {"id": "1", "label": "Science", "value": "science"},
                {"id": "2", "label": "Commerce", "value": "commerce"},
                {"id": "3", "label": "Arts", "value": "arts"},
                {"id": "4", "label": "General", "value": "general"}
            ]
        },
        {
            "id": "grade_level",
            "field_type": FieldType.NUMBER,
            "label": "Grade Level",
            "field_name": "grade_level",
            "placeholder": "Enter grade level (1-12)",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True,
                "min": 1,
                "max": 12
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
            "id": "max_students",
            "field_type": FieldType.NUMBER,
            "label": "Maximum Students",
            "field_name": "max_students",
            "placeholder": "Enter maximum number of students",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False,
                "min": 1,
                "max": 100
            }
        },
        {
            "id": "room_number",
            "field_type": FieldType.TEXT,
            "label": "Room Number",
            "field_name": "room_number",
            "placeholder": "Enter room number",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False,
                "maxLength": 20
            }
        },
        {
            "id": "class_teacher_id",
            "field_type": FieldType.NUMBER,
            "label": "Class Teacher ID",
            "field_name": "class_teacher_id",
            "placeholder": "Enter class teacher ID",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": False,
            "validation_rules": {
                "required": False,
                "min": 1
            }
        }
    ]
}

# Default assignment form based on Assignment schema
DEFAULT_ASSIGNMENT_FORM = {
    "name": "Assignment Form",
    "key": "assignment_form",
    "description": "Default form for assignment creation and management",
    "entityType": "assignment",
    "fields": [
        {
            "id": "title",
            "field_type": FieldType.TEXT,
            "label": "Assignment Title",
            "field_name": "title",
            "placeholder": "Enter assignment title",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True,
                "minLength": 1,
                "maxLength": 200
            }
        },
        {
            "id": "description",
            "field_type": FieldType.TEXTAREA,
            "label": "Description",
            "field_name": "description",
            "placeholder": "Enter assignment description",
            "is_required": False,
            "is_filterable": False,
            "is_visible_in_listing": False,
            "validation_rules": {
                "required": False,
                "maxLength": 1000
            }
        },
        {
            "id": "class_id",
            "field_type": FieldType.NUMBER,
            "label": "Class ID",
            "field_name": "class_id",
            "placeholder": "Enter class ID",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": False,
            "validation_rules": {
                "required": True,
                "min": 1
            }
        },
        {
            "id": "subject_id",
            "field_type": FieldType.NUMBER,
            "label": "Subject ID",
            "field_name": "subject_id",
            "placeholder": "Enter subject ID",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": False,
            "validation_rules": {
                "required": True,
                "min": 1
            }
        },
        {
            "id": "teacher_id",
            "field_type": FieldType.NUMBER,
            "label": "Teacher ID",
            "field_name": "teacher_id",
            "placeholder": "Enter teacher ID",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": False,
            "validation_rules": {
                "required": True,
                "min": 1
            }
        },
        {
            "id": "due_date",
            "field_type": FieldType.DATE,
            "label": "Due Date",
            "field_name": "due_date",
            "placeholder": "Select due date",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            }
        },
        {
            "id": "instructions",
            "field_type": FieldType.TEXTAREA,
            "label": "Instructions",
            "field_name": "instructions",
            "placeholder": "Enter assignment instructions",
            "is_required": False,
            "is_filterable": False,
            "is_visible_in_listing": False,
            "validation_rules": {
                "required": False,
                "maxLength": 2000
            }
        },
        {
            "id": "max_score",
            "field_type": FieldType.NUMBER,
            "label": "Maximum Score",
            "field_name": "max_score",
            "placeholder": "Enter maximum score",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False,
                "min": 0,
                "max": 100
            }
        },
        {
            "id": "is_published",
            "field_type": FieldType.CHECKBOX,
            "label": "Published",
            "field_name": "is_published",
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

# Default exam form based on Exam schema
DEFAULT_EXAM_FORM = {
    "name": "Exam Form",
    "key": "exam_form",
    "description": "Default form for exam creation and management",
    "entityType": "exam",
    "fields": [
        {
            "id": "name",
            "field_type": FieldType.TEXT,
            "label": "Exam Name",
            "field_name": "name",
            "placeholder": "Enter exam name",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True,
                "minLength": 1,
                "maxLength": 200
            }
        },
        {
            "id": "description",
            "field_type": FieldType.TEXTAREA,
            "label": "Description",
            "field_name": "description",
            "placeholder": "Enter exam description",
            "is_required": False,
            "is_filterable": False,
            "is_visible_in_listing": False,
            "validation_rules": {
                "required": False,
                "maxLength": 1000
            }
        },
        {
            "id": "exam_id",
            "field_type": FieldType.TEXT,
            "label": "Exam ID",
            "field_name": "exam_id",
            "placeholder": "Enter unique exam ID",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True,
                "minLength": 1,
                "maxLength": 50
            }
        },
        {
            "id": "class_id",
            "field_type": FieldType.NUMBER,
            "label": "Class ID",
            "field_name": "class_id",
            "placeholder": "Enter class ID",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": False,
            "validation_rules": {
                "required": True,
                "min": 1
            }
        },
        {
            "id": "exam_date",
            "field_type": FieldType.DATE,
            "label": "Exam Date",
            "field_name": "exam_date",
            "placeholder": "Select exam date",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            }
        },
        {
            "id": "start_time",
            "field_type": FieldType.TEXT,
            "label": "Start Time",
            "field_name": "start_time",
            "placeholder": "Enter start time (e.g., 09:00 AM)",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            }
        },
        {
            "id": "end_time",
            "field_type": FieldType.TEXT,
            "label": "End Time",
            "field_name": "end_time",
            "placeholder": "Enter end time (e.g., 10:30 AM)",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            }
        },
        {
            "id": "duration_minutes",
            "field_type": FieldType.NUMBER,
            "label": "Duration (Minutes)",
            "field_name": "duration_minutes",
            "placeholder": "Enter duration in minutes",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True,
                "min": 30,
                "max": 480
            }
        },
        {
            "id": "total_marks",
            "field_type": FieldType.NUMBER,
            "label": "Total Marks",
            "field_name": "total_marks",
            "placeholder": "Enter total marks",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True,
                "min": 1,
                "max": 1000
            }
        },
        {
            "id": "passing_marks",
            "field_type": FieldType.NUMBER,
            "label": "Passing Marks",
            "field_name": "passing_marks",
            "placeholder": "Enter passing marks",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False,
                "min": 0
            }
        },
        {
            "id": "instructions",
            "field_type": FieldType.TEXTAREA,
            "label": "Instructions",
            "field_name": "instructions",
            "placeholder": "Enter exam instructions",
            "is_required": False,
            "is_filterable": False,
            "is_visible_in_listing": False,
            "validation_rules": {
                "required": False,
                "maxLength": 2000
            }
        },
        {
            "id": "status",
            "field_type": FieldType.SELECT,
            "label": "Status",
            "field_name": "status",
            "placeholder": "Select exam status",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            },
            "options": [
                {"id": "1", "label": "Upcoming", "value": "upcoming"},
                {"id": "2", "label": "Ongoing", "value": "ongoing"},
                {"id": "3", "label": "Completed", "value": "completed"},
                {"id": "4", "label": "Cancelled", "value": "cancelled"}
            ]
        }
    ]
}

# Dictionary mapping entity types to their default forms
DEFAULT_FORMS: Dict[str, Dict[str, Any]] = {
    "student": DEFAULT_STUDENT_FORM,
    "teacher": DEFAULT_TEACHER_FORM,
    "class": DEFAULT_CLASS_FORM,
    "assignment": DEFAULT_ASSIGNMENT_FORM,
    "exam": DEFAULT_EXAM_FORM,
    # Add more default forms for other entities here
}

def get_default_form(entity_type: str) -> Dict[str, Any]:
    """Get the default form schema for a given entity type"""
    return DEFAULT_FORMS.get(entity_type, {})

def get_default_form_fields(entity_type: str) -> list:
    """Get the default form fields for a given entity type"""
    default_form = get_default_form(entity_type)
    return default_form.get("fields", [])
