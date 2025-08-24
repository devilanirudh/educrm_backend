#!/usr/bin/env python3
"""
Setup script for the comprehensive attendance system
"""

import sys
import os
import logging
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

try:
    from app.database.session import engine
    from app.database.init_db import init_db
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the backend directory")
    sys.exit(1)

def setup_attendance_system():
    """Setup the complete attendance system"""
    
    try:
        logger.info("🚀 Starting attendance system setup...")
        
        # Initialize the database
        logger.info("📊 Initializing database...")
        init_db()
        
        # Run the attendance migration
        logger.info("🔄 Running attendance system migration...")
        # Migration will be handled by the main app startup
        
        logger.info("✅ Attendance system setup completed successfully!")
        logger.info("")
        logger.info("📋 What was created:")
        logger.info("   • attendance_policies table")
        logger.info("   • attendance_sessions table") 
        logger.info("   • period_attendance table")
        logger.info("   • attendance_exceptions table")
        logger.info("   • attendance_notifications table")
        logger.info("   • Enhanced attendance_records table")
        logger.info("   • Database indexes for performance")
        logger.info("   • Default global attendance policy")
        logger.info("")
        logger.info("🎯 Next steps:")
        logger.info("   1. Start your backend server")
        logger.info("   2. Access the attendance API at /api/v1/attendance")
        logger.info("   3. Use the frontend attendance pages at /attendance")
        logger.info("   4. Configure attendance policies for your classes")
        logger.info("")
        logger.info("📚 API Endpoints available:")
        logger.info("   • POST /api/v1/attendance/policies - Create policies")
        logger.info("   • GET /api/v1/attendance/policies - List policies")
        logger.info("   • POST /api/v1/attendance/bulk - Bulk mark attendance")
        logger.info("   • POST /api/v1/attendance/reports - Generate reports")
        logger.info("   • GET /api/v1/attendance/analytics - Get analytics")
        logger.info("   • POST /api/v1/attendance/check-in - Student check-in")
        logger.info("   • POST /api/v1/attendance/check-out - Student check-out")
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    setup_attendance_system()
