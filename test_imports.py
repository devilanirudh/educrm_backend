#!/usr/bin/env python3
"""
Test script to verify imports work correctly
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_imports():
    """Test all the imports used in the classes API"""
    try:
        print("Testing imports...")
        
        # Test core imports
        from app.core.permissions import UserRole
        print("✅ UserRole imported successfully")
        
        from app.api.deps import get_current_user
        print("✅ get_current_user imported successfully")
        
        from app.database.session import get_db
        print("✅ get_db imported successfully")
        
        # Test model imports
        from app.models.academic import Class, ClassSubject, Subject
        print("✅ Academic models imported successfully")
        
        from app.models.student import Student
        print("✅ Student model imported successfully")
        
        from app.models.teacher import Teacher
        print("✅ Teacher model imported successfully")
        
        from app.models.user import User
        print("✅ User model imported successfully")
        
        # Test schema imports
        from app.schemas.classes import (
            ClassCreate, 
            ClassUpdate, 
            ClassResponse, 
            ClassListResponse,
            ClassSubjectCreate,
            ClassSubjectResponse
        )
        print("✅ Class schemas imported successfully")
        
        # Test classes API
        from app.api.v1.classes import router
        print("✅ Classes router imported successfully")
        
        print("\n🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)


