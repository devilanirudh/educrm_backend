#!/usr/bin/env python3
"""
Test script to verify cascading delete functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.user import User, Parent
from app.models.student import Student
from app.models.teacher import Teacher
from app.core.permissions import UserRole
from datetime import date

def test_cascade_delete():
    """Test cascading delete functionality"""
    
    print("🧪 Testing cascading delete functionality...")
    
    db = SessionLocal()
    
    try:
        # Test 1: Delete student profile should delete user
        print("\n📝 Test 1: Delete student profile -> should delete user")
        
        # Create a test student
        test_user = User(
            email="test.student@example.com",
            first_name="Test",
            last_name="Student",
            role=UserRole.STUDENT,
            is_active=True
        )
        db.add(test_user)
        db.flush()
        
        test_student = Student(
            user_id=test_user.id,
            student_id="TEST001",
            admission_date=date.today(),
            academic_year="2024-2025"
        )
        db.add(test_student)
        db.flush()
        
        print(f"✅ Created test student with user_id: {test_user.id}, student_id: {test_student.id}")
        
        # Delete the student
        db.delete(test_student)
        db.commit()
        
        # Check if user was also deleted
        user_exists = db.query(User).filter(User.id == test_user.id).first()
        if user_exists:
            print("❌ FAIL: User still exists after student deletion")
        else:
            print("✅ PASS: User was automatically deleted when student was deleted")
        
        # Test 2: Delete user should delete student profile
        print("\n📝 Test 2: Delete user -> should delete student profile")
        
        # Create another test student
        test_user2 = User(
            email="test.student2@example.com",
            first_name="Test",
            last_name="Student2",
            role=UserRole.STUDENT,
            is_active=True
        )
        db.add(test_user2)
        db.flush()
        
        test_student2 = Student(
            user_id=test_user2.id,
            student_id="TEST002",
            admission_date=date.today(),
            academic_year="2024-2025"
        )
        db.add(test_student2)
        db.flush()
        
        print(f"✅ Created test student2 with user_id: {test_user2.id}, student_id: {test_student2.id}")
        
        # Delete the user
        db.delete(test_user2)
        db.commit()
        
        # Check if student was also deleted
        student_exists = db.query(Student).filter(Student.id == test_student2.id).first()
        if student_exists:
            print("❌ FAIL: Student still exists after user deletion")
        else:
            print("✅ PASS: Student was automatically deleted when user was deleted")
        
        # Test 3: Delete teacher profile should delete user
        print("\n📝 Test 3: Delete teacher profile -> should delete user")
        
        # Create a test teacher
        test_teacher_user = User(
            email="test.teacher@example.com",
            first_name="Test",
            last_name="Teacher",
            role=UserRole.TEACHER,
            is_active=True
        )
        db.add(test_teacher_user)
        db.flush()
        
        test_teacher = Teacher(
            user_id=test_teacher_user.id,
            employee_id="TEMP001",
            hire_date=date.today(),
            employment_type="permanent"
        )
        db.add(test_teacher)
        db.flush()
        
        print(f"✅ Created test teacher with user_id: {test_teacher_user.id}, teacher_id: {test_teacher.id}")
        
        # Delete the teacher
        db.delete(test_teacher)
        db.commit()
        
        # Check if user was also deleted
        teacher_user_exists = db.query(User).filter(User.id == test_teacher_user.id).first()
        if teacher_user_exists:
            print("❌ FAIL: Teacher user still exists after teacher deletion")
        else:
            print("✅ PASS: Teacher user was automatically deleted when teacher was deleted")
        
        print("\n🎉 All cascade delete tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_cascade_delete()
