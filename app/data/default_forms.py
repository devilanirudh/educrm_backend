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
            "field_type": FieldType.SELECT,
            "label": "Academic Year",
            "field_name": "academic_year",
            "placeholder": "Select academic year",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            },
            "options": [
                {"id": "1", "label": "2024-2025", "value": "2024-2025"},
                {"id": "2", "label": "2023-2024", "value": "2023-2024"},
                {"id": "3", "label": "2022-2023", "value": "2022-2023"},
                {"id": "4", "label": "2021-2022", "value": "2021-2022"},
                {"id": "5", "label": "2020-2021", "value": "2020-2021"}
            ]
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
            "field_type": FieldType.SELECT,
            "label": "Section",
            "field_name": "section",
            "placeholder": "Select section",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False
            },
            "options": [
                {"id": "1", "label": "A", "value": "A"},
                {"id": "2", "label": "B", "value": "B"},
                {"id": "3", "label": "C", "value": "C"},
                {"id": "4", "label": "D", "value": "D"},
                {"id": "5", "label": "E", "value": "E"},
                {"id": "6", "label": "F", "value": "F"}
            ]
        },
        {
            "id": "grade_level",
            "field_type": FieldType.SELECT,
            "label": "Grade Level",
            "field_name": "grade_level",
            "placeholder": "Select grade level",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            },
            "options": [
                {"id": "1", "label": "Grade 1", "value": "1"},
                {"id": "2", "label": "Grade 2", "value": "2"},
                {"id": "3", "label": "Grade 3", "value": "3"},
                {"id": "4", "label": "Grade 4", "value": "4"},
                {"id": "5", "label": "Grade 5", "value": "5"},
                {"id": "6", "label": "Grade 6", "value": "6"},
                {"id": "7", "label": "Grade 7", "value": "7"},
                {"id": "8", "label": "Grade 8", "value": "8"},
                {"id": "9", "label": "Grade 9", "value": "9"},
                {"id": "10", "label": "Grade 10", "value": "10"},
                {"id": "11", "label": "Grade 11", "value": "11"},
                {"id": "12", "label": "Grade 12", "value": "12"}
            ]
        },
        {
            "id": "parent_email",
            "field_type": FieldType.EMAIL,
            "label": "Parent Email",
            "field_name": "parent_email",
            "placeholder": "Enter parent email address",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True,
                "type": "email"
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
            "id": "subjects",
            "field_type": FieldType.MULTI_SELECT,
            "label": "Subjects I Can Teach",
            "field_name": "subjects",
            "placeholder": "Select subjects you can teach",
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
                {"id": "4", "label": "Social Studies", "value": "social_studies"},
                {"id": "5", "label": "Physical Education", "value": "physical_education"},
                {"id": "6", "label": "Art", "value": "art"},
                {"id": "7", "label": "Music", "value": "music"}
            ]
        },
        {
            "id": "assigned_classes",
            "field_type": FieldType.MULTI_SELECT,
            "label": "Classes I Teach",
            "field_name": "assigned_classes",
            "placeholder": "Select classes you are assigned to teach",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False
            },
            "options": [
                {"id": "1", "label": "Grade 1 A", "value": "grade_1_a"},
                {"id": "2", "label": "Grade 1 B", "value": "grade_1_b"},
                {"id": "3", "label": "Grade 2 A", "value": "grade_2_a"},
                {"id": "4", "label": "Grade 3 A", "value": "grade_3_a"},
                {"id": "5", "label": "Grade 4 A", "value": "grade_4_a"},
                {"id": "6", "label": "Grade 5 A", "value": "grade_5_a"}
            ]
        },
        {
            "id": "class_assignments",
            "field_type": FieldType.DYNAMIC_CONFIG,
            "label": "Class-Subject Assignments",
            "field_name": "class_assignments",
            "placeholder": "Configure your class and subject assignments",
            "is_required": False,
            "is_filterable": False,
            "is_visible_in_listing": False,
            "validation_rules": {
                "required": False
            },
            "config": {
                "type": "class_subject_assignments",
                "fields": [
                    {
                        "name": "class",
                        "type": "select",
                        "label": "Class",
                        "options": [
                            {"value": "1", "label": "Grade 1"},
                            {"value": "2", "label": "Grade 2"},
                            {"value": "3", "label": "Grade 3"},
                            {"value": "4", "label": "Grade 4"},
                            {"value": "5", "label": "Grade 5"}
                        ]
                    },
                    {
                        "name": "section",
                        "type": "select",
                        "label": "Section",
                        "options": [
                            {"value": "A", "label": "A"},
                            {"value": "B", "label": "B"},
                            {"value": "C", "label": "C"}
                        ]
                    },
                    {
                        "name": "subject",
                        "type": "select",
                        "label": "Subject",
                        "options": [
                            {"value": "mathematics", "label": "Mathematics"},
                            {"value": "english", "label": "English"},
                            {"value": "science", "label": "Science"},
                            {"value": "social_studies", "label": "Social Studies"},
                            {"value": "physical_education", "label": "Physical Education"},
                            {"value": "art", "label": "Art"},
                            {"value": "music", "label": "Music"}
                        ]
                    }
                ]
            }
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
            "field_type": FieldType.SELECT,
            "label": "Class Name",
            "field_name": "name",
            "placeholder": "Select class name",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            },
            "options": [
                {"id": "1", "label": "Grade 1", "value": "Grade 1"},
                {"id": "2", "label": "Grade 2", "value": "Grade 2"},
                {"id": "3", "label": "Grade 3", "value": "Grade 3"},
                {"id": "4", "label": "Grade 4", "value": "Grade 4"},
                {"id": "5", "label": "Grade 5", "value": "Grade 5"},
                {"id": "6", "label": "Grade 6", "value": "Grade 6"},
                {"id": "7", "label": "Grade 7", "value": "Grade 7"},
                {"id": "8", "label": "Grade 8", "value": "Grade 8"},
                {"id": "9", "label": "Grade 9", "value": "Grade 9"},
                {"id": "10", "label": "Grade 10", "value": "Grade 10"},
                {"id": "11", "label": "Grade 11", "value": "Grade 11"},
                {"id": "12", "label": "Grade 12", "value": "Grade 12"}
            ]
        },
        {
            "id": "section",
            "field_type": FieldType.SELECT,
            "label": "Section",
            "field_name": "section",
            "placeholder": "Select section",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            },
            "options": [
                {"id": "1", "label": "A", "value": "A"},
                {"id": "2", "label": "B", "value": "B"},
                {"id": "3", "label": "C", "value": "C"},
                {"id": "4", "label": "D", "value": "D"},
                {"id": "5", "label": "E", "value": "E"},
                {"id": "6", "label": "F", "value": "F"}
            ]
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
                {"id": "1", "label": "Science", "value": "Science"},
                {"id": "2", "label": "Commerce", "value": "Commerce"},
                {"id": "3", "label": "Arts", "value": "Arts"},
                {"id": "4", "label": "General", "value": "General"}
            ]
        },
        {
            "id": "grade_level",
            "field_type": FieldType.SELECT,
            "label": "Grade Level",
            "field_name": "grade_level",
            "placeholder": "Select grade level",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            },
            "options": [
                {"id": "1", "label": "1", "value": "1"},
                {"id": "2", "label": "2", "value": "2"},
                {"id": "3", "label": "3", "value": "3"},
                {"id": "4", "label": "4", "value": "4"},
                {"id": "5", "label": "5", "value": "5"},
                {"id": "6", "label": "6", "value": "6"},
                {"id": "7", "label": "7", "value": "7"},
                {"id": "8", "label": "8", "value": "8"},
                {"id": "9", "label": "9", "value": "9"},
                {"id": "10", "label": "10", "value": "10"},
                {"id": "11", "label": "11", "value": "11"},
                {"id": "12", "label": "12", "value": "12"}
            ]
        },
        {
            "id": "academic_year",
            "field_type": FieldType.SELECT,
            "label": "Academic Year",
            "field_name": "academic_year",
            "placeholder": "Select academic year",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            },
            "options": [
                {"id": "1", "label": "2024-2025", "value": "2024-2025"},
                {"id": "2", "label": "2025-2026", "value": "2025-2026"},
                {"id": "3", "label": "2026-2027", "value": "2026-2027"},
                {"id": "4", "label": "2027-2028", "value": "2027-2028"},
                {"id": "5", "label": "2028-2029", "value": "2028-2029"}
            ]
        },
        {
            "id": "max_students",
            "field_type": FieldType.SELECT,
            "label": "Maximum Students",
            "field_name": "max_students",
            "placeholder": "Select maximum students",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False
            },
            "options": [
                {"id": "1", "label": "20", "value": "20"},
                {"id": "2", "label": "25", "value": "25"},
                {"id": "3", "label": "30", "value": "30"},
                {"id": "4", "label": "35", "value": "35"},
                {"id": "5", "label": "40", "value": "40"},
                {"id": "6", "label": "45", "value": "45"},
                {"id": "7", "label": "50", "value": "50"}
            ]
        },
        {
            "id": "room_number",
            "field_type": FieldType.SELECT,
            "label": "Room Number",
            "field_name": "room_number",
            "placeholder": "Select room number",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False
            },
            "options": [
                {"id": "1", "label": "Room 101", "value": "101"},
                {"id": "2", "label": "Room 102", "value": "102"},
                {"id": "3", "label": "Room 103", "value": "103"},
                {"id": "4", "label": "Room 104", "value": "104"},
                {"id": "5", "label": "Room 105", "value": "105"},
                {"id": "6", "label": "Room 201", "value": "201"},
                {"id": "7", "label": "Room 202", "value": "202"},
                {"id": "8", "label": "Room 203", "value": "203"},
                {"id": "9", "label": "Room 204", "value": "204"},
                {"id": "10", "label": "Room 205", "value": "205"},
                {"id": "11", "label": "Room 301", "value": "301"},
                {"id": "12", "label": "Room 302", "value": "302"},
                {"id": "13", "label": "Room 303", "value": "303"},
                {"id": "14", "label": "Room 304", "value": "304"},
                {"id": "15", "label": "Room 305", "value": "305"}
            ]
        },
        {
            "id": "class_teacher_id",
            "field_type": FieldType.SELECT,
            "label": "Class Teacher",
            "field_name": "class_teacher_id",
            "placeholder": "Select class teacher",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": False,
            "validation_rules": {
                "required": False
            },
            "options": []
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
            "id": "teacher_id",
            "field_type": FieldType.SELECT,
            "label": "Teacher",
            "field_name": "teacher_id",
            "placeholder": "Select teacher",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            },
            "options": []  # Will be populated dynamically
        },
        {
            "id": "class_id",
            "field_type": FieldType.SELECT,
            "label": "Class",
            "field_name": "class_id",
            "placeholder": "Select class",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            },
            "options": []  # Will be populated dynamically
        },
        {
            "id": "subject_id",
            "field_type": FieldType.SELECT,
            "label": "Subject",
            "field_name": "subject_id",
            "placeholder": "Select subject",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            },
            "options": []  # Will be populated dynamically
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
        },
        {
            "id": "status",
            "field_type": FieldType.SELECT,
            "label": "Status",
            "field_name": "status",
            "placeholder": "Select status",
            "is_required": False,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": False
            },
            "options": [
                {"id": 1, "value": "pending", "label": "Pending", "order": 1},
                {"id": 2, "value": "submitted", "label": "Submitted", "order": 2},
                {"id": 3, "value": "overdue", "label": "Overdue", "order": 3},
                {"id": 4, "value": "graded", "label": "Graded", "order": 4}
            ]
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
            "id": "teacher_id",
            "field_type": FieldType.SELECT,
            "label": "Teacher",
            "field_name": "teacher_id",
            "placeholder": "Select teacher",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            },
            "options": []
        },
        {
            "id": "class_id",
            "field_type": FieldType.SELECT,
            "label": "Class",
            "field_name": "class_id",
            "placeholder": "Select class",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            },
            "options": []
        },
        {
            "id": "subject_id",
            "field_type": FieldType.SELECT,
            "label": "Subject",
            "field_name": "subject_id",
            "placeholder": "Select subject",
            "is_required": True,
            "is_filterable": True,
            "is_visible_in_listing": True,
            "validation_rules": {
                "required": True
            },
            "options": []
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
                {"id": "1", "label": "Draft", "value": "draft"},
                {"id": "2", "label": "Published", "value": "published"},
                {"id": "3", "label": "Active", "value": "active"},
                {"id": "4", "label": "Completed", "value": "completed"},
                {"id": "5", "label": "Cancelled", "value": "cancelled"}
            ]
        },
        {
            "id": "exam_materials",
            "field_type": FieldType.FILE,
            "label": "Exam Materials",
            "field_name": "exam_materials",
            "placeholder": "Upload exam materials (PDF, DOC, etc.)",
            "is_required": False,
            "is_filterable": False,
            "is_visible_in_listing": False,
            "validation_rules": {
                "required": False,
                "fileTypes": ["pdf", "doc", "docx", "txt"],
                "maxSize": 10485760  # 10MB
            }
        },
        {
            "id": "exam_image",
            "field_type": FieldType.IMAGE,
            "label": "Exam Image",
            "field_name": "exam_image",
            "placeholder": "Upload exam image",
            "is_required": False,
            "is_filterable": False,
            "is_visible_in_listing": False,
            "validation_rules": {
                "required": False,
                "fileTypes": ["jpg", "jpeg", "png", "gif"],
                "maxSize": 5242880  # 5MB
            }
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
