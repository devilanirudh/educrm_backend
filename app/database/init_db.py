"""
Database initialization and sample data creation
"""

from sqlalchemy.orm import Session
from app.database.session import engine, SessionLocal, Base
from app.core.security import get_password_hash
from app.core.permissions import UserRole
from app.models.user import User, Parent
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.academic import Subject, Class, ClassSubject
from app.models.financial import FeeStructure, FeeType
from app.models.content import CMSPage, NewsArticle
from app.models.communication import Notification
from app.models.transport import BusRoute, BusStop, Bus, Driver
from app.models.library import Book, LibraryTransaction
from app.models.hostel import HostelBlock, HostelRoom, HostelAllocation
import logging
from datetime import date, datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Create all database tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

def create_sample_data():
    """Create sample data for development and testing"""
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(User).filter(User.email == "admin@school.edu").first():
            logger.info("Sample data already exists, skipping creation")
            return
        
        logger.info("Creating sample data...")
        
        # Create Admin User
        admin_user = User(
            email="admin@school.edu",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            first_name="System",
            last_name="Administrator",
            phone="+1234567890",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            address="123 School Street",
            city="Education City",
            state="ED",
            country="USA",
            postal_code="12345"
        )
        db.add(admin_user)
        db.flush()
        
        # Create Sample Teacher
        teacher_user = User(
            email="teacher@school.edu",
            username="teacher1",
            hashed_password=get_password_hash("teacher123"),
            first_name="John",
            last_name="Smith",
            phone="+1234567891",
            role=UserRole.TEACHER,
            is_active=True,
            is_verified=True,
            date_of_birth=datetime(1985, 5, 15),
            gender="Male",
            address="456 Teacher Lane",
            city="Education City",
            state="ED",
            country="USA",
            postal_code="12345"
        )
        db.add(teacher_user)
        db.flush()
        
        teacher = Teacher(
            user_id=teacher_user.id,
            employee_id="EMP001",
            qualifications="M.Sc. Mathematics",
            specialization="Mathematics",
            experience=10,
            hire_date=date(2020, 8, 1),
            department="Mathematics",
            designation="Senior Teacher",
            employment_type="permanent",
            salary=50000.0
        )
        db.add(teacher)
        db.flush()
        
        # Create Sample Parent
        parent_user = User(
            email="parent@school.edu",
            username="parent1",
            hashed_password=get_password_hash("parent123"),
            first_name="Mary",
            last_name="Johnson",
            phone="+1234567892",
            role=UserRole.PARENT,
            is_active=True,
            is_verified=True,
            date_of_birth=datetime(1980, 3, 20),
            gender="Female",
            address="789 Parent Avenue",
            city="Education City",
            state="ED",
            country="USA",
            postal_code="12345"
        )
        db.add(parent_user)
        db.flush()
        
        parent = Parent(
            user_id=parent_user.id,
            occupation="Software Engineer",
            workplace="Tech Corp",
            work_phone="+1234567893",
            relationship_to_student="Mother",
            is_primary_contact=True
        )
        db.add(parent)
        db.flush()
        
        # Create Sample Student
        student_user = User(
            email="student@school.edu",
            username="student1",
            hashed_password=get_password_hash("student123"),
            first_name="Alice",
            last_name="Johnson",
            phone="+1234567894",
            role=UserRole.STUDENT,
            is_active=True,
            is_verified=True,
            date_of_birth=datetime(2010, 7, 10),
            gender="Female",
            address="789 Parent Avenue",
            city="Education City",
            state="ED",
            country="USA",
            postal_code="12345"
        )
        db.add(student_user)
        db.flush()
        
        # Create Subjects
        subjects_data = [
            {"name": "Mathematics", "code": "MATH", "department": "Science", "category": "core"},
            {"name": "English", "code": "ENG", "department": "Languages", "category": "core"},
            {"name": "Science", "code": "SCI", "department": "Science", "category": "core"},
            {"name": "Social Studies", "code": "SS", "department": "Social Sciences", "category": "core"},
            {"name": "Physical Education", "code": "PE", "department": "Sports", "category": "core"},
            {"name": "Art", "code": "ART", "department": "Arts", "category": "elective"},
            {"name": "Music", "code": "MUS", "department": "Arts", "category": "elective"},
        ]
        
        subjects = []
        for subject_data in subjects_data:
            subject = Subject(**subject_data)
            db.add(subject)
            subjects.append(subject)
        db.flush()
        
        # Create Classes
        classes_data = [
            {"name": "Grade 1", "section": "A", "grade_level": 1, "academic_year": "2024-2025", "max_students": 30},
            {"name": "Grade 1", "section": "B", "grade_level": 1, "academic_year": "2024-2025", "max_students": 30},
            {"name": "Grade 2", "section": "A", "grade_level": 2, "academic_year": "2024-2025", "max_students": 30},
            {"name": "Grade 3", "section": "A", "grade_level": 3, "academic_year": "2024-2025", "max_students": 30},
            {"name": "Grade 4", "section": "A", "grade_level": 4, "academic_year": "2024-2025", "max_students": 30},
            {"name": "Grade 5", "section": "A", "grade_level": 5, "academic_year": "2024-2025", "max_students": 30},
        ]
        
        classes = []
        for class_data in classes_data:
            class_obj = Class(class_teacher_id=teacher.id, **class_data)
            db.add(class_obj)
            classes.append(class_obj)
        db.flush()
        
        # Assign subjects to classes
        for class_obj in classes:
            for subject in subjects:
                class_subject = ClassSubject(
                    class_id=class_obj.id,
                    subject_id=subject.id,
                    teacher_id=teacher.id,
                    weekly_hours=5 if subject.category == "core" else 2
                )
                db.add(class_subject)
        
        # Create student and assign to class
        student = Student(
            user_id=student_user.id,
            student_id="STU001",
            admission_date=date(2024, 8, 1),
            current_class_id=classes[0].id,  # Grade 1 A
            academic_year="2024-2025",
            roll_number="001",
            blood_group="O+",
            transportation_mode="bus"
        )
        db.add(student)
        db.flush()
        
        # Link parent and student
        parent.children.append(student)
        
        # Create Fee Types
        fee_types_data = [
            {"name": "Tuition Fee", "description": "Monthly tuition fee", "is_mandatory": True},
            {"name": "Transport Fee", "description": "School bus transportation fee", "is_mandatory": False},
            {"name": "Library Fee", "description": "Library and books fee", "is_mandatory": True},
            {"name": "Sports Fee", "description": "Sports and physical education fee", "is_mandatory": False},
            {"name": "Admission Fee", "description": "One-time admission fee", "is_mandatory": True},
        ]
        
        fee_types = []
        for fee_type_data in fee_types_data:
            fee_type = FeeType(**fee_type_data)
            db.add(fee_type)
            fee_types.append(fee_type)
        db.flush()
        
        # Create Fee Structures
        for class_obj in classes:
            # Tuition Fee
            tuition_fee = FeeStructure(
                fee_type_id=fee_types[0].id,  # Tuition Fee
                class_id=class_obj.id,
                academic_year="2024-2025",
                amount=500.00,
                due_date=date(2024, 9, 1),
                frequency="monthly"
            )
            db.add(tuition_fee)
            
            # Library Fee
            library_fee = FeeStructure(
                fee_type_id=fee_types[2].id,  # Library Fee
                class_id=class_obj.id,
                academic_year="2024-2025",
                amount=100.00,
                due_date=date(2024, 8, 15),
                frequency="annual"
            )
            db.add(library_fee)
        
        # Create CMS Pages
        cms_pages_data = [
            {
                "title": "Welcome to Our School",
                "slug": "welcome",
                "content": "<h1>Welcome to Our School</h1><p>We are committed to providing quality education...</p>",
                "page_type": "page",
                "is_published": True,
                "author_id": admin_user.id
            },
            {
                "title": "About Us",
                "slug": "about",
                "content": "<h1>About Our School</h1><p>Founded in 1950, our school has a rich history...</p>",
                "page_type": "page",
                "is_published": True,
                "author_id": admin_user.id
            },
            {
                "title": "Admissions",
                "slug": "admissions",
                "content": "<h1>Admissions</h1><p>We welcome applications from students...</p>",
                "page_type": "page",
                "is_published": True,
                "author_id": admin_user.id
            }
        ]
        
        for page_data in cms_pages_data:
            cms_page = CMSPage(**page_data)
            db.add(cms_page)
        
        # Create News Articles
        news_articles_data = [
            {
                "title": "New Academic Year Begins",
                "slug": "new-academic-year-2024",
                "content": "<p>We are excited to announce the beginning of the new academic year 2024-2025...</p>",
                "excerpt": "New academic year starts with exciting programs and activities.",
                "is_published": True,
                "author_id": admin_user.id
            },
            {
                "title": "Sports Day Announcement",
                "slug": "sports-day-2024",
                "content": "<p>Our annual sports day will be held on October 15, 2024...</p>",
                "excerpt": "Annual sports day scheduled for October 15, 2024.",
                "is_published": True,
                "author_id": admin_user.id
            }
        ]
        
        for article_data in news_articles_data:
            news_article = NewsArticle(**article_data)
            db.add(news_article)
        
        # Create Sample Notifications
        notifications_data = [
            {
                "user_id": student_user.id,
                "title": "Welcome to School Portal",
                "message": "Welcome to our school management system. You can now access assignments, grades, and more.",
                "notification_type": "info"
            },
            {
                "user_id": parent_user.id,
                "title": "Parent Portal Access",
                "message": "You now have access to track your child's progress, fees, and school communications.",
                "notification_type": "info"
            },
            {
                "user_id": teacher_user.id,
                "title": "Teacher Dashboard Ready",
                "message": "Your teacher dashboard is ready. You can now manage classes, assignments, and student grades.",
                "notification_type": "info"
            }
        ]
        
        for notification_data in notifications_data:
            notification = Notification(**notification_data)
            db.add(notification)
        
        db.commit()
        logger.info("Sample data created successfully")
        
        # Print login credentials
        print("\n" + "="*50)
        print("SAMPLE LOGIN CREDENTIALS")
        print("="*50)
        print("Admin:")
        print("  Email: admin@school.edu")
        print("  Password: admin123")
        print("\nTeacher:")
        print("  Email: teacher@school.edu")
        print("  Password: teacher123")
        print("\nParent:")
        print("  Email: parent@school.edu")
        print("  Password: parent123")
        print("\nStudent:")
        print("  Email: student@school.edu")
        print("  Password: student123")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize the database with tables and sample data"""
    logger.info("Initializing database...")
    
    try:
        # Create tables
        create_tables()
        
        # Create sample data
        create_sample_data()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    init_db()
