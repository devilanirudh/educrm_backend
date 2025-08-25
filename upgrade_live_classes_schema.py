#!/usr/bin/env python3
"""
Live Classes Schema Upgrade Script
This script safely upgrades the live classes schema to include Jitsi Meet integration.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import json

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LiveClassesSchemaUpgrader:
    """Handles the upgrade of live classes schema with Jitsi integration"""
    
    def __init__(self):
        # Use the eschool.db database file
        self.engine = create_engine('sqlite:///./eschool.db')
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.inspector = inspect(self.engine)
        
    def check_existing_tables(self):
        """Check if required tables exist"""
        logger.info("Checking existing tables...")
        
        required_tables = ['live_classes', 'class_attendance', 'users', 'classes']
        existing_tables = self.inspector.get_table_names()
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            logger.error(f"Missing required tables: {missing_tables}")
            return False
            
        logger.info("All required tables exist")
        return True
    
    def check_existing_columns(self, table_name):
        """Check existing columns in a table"""
        if not self.inspector.has_table(table_name):
            return []
        
        columns = self.inspector.get_columns(table_name)
        return [col['name'] for col in columns]
    
    def check_if_upgrade_needed(self):
        """Check if the upgrade is actually needed"""
        logger.info("Checking if upgrade is needed...")
        
        live_classes_columns = self.check_existing_columns('live_classes')
        attendance_columns = self.check_existing_columns('class_attendance')
        
        required_live_class_fields = [
            'jitsi_room_name', 'jitsi_meeting_url', 'jitsi_settings', 'jitsi_token',
            'description', 'max_participants', 'enable_chat', 'enable_whiteboard'
        ]
        
        required_attendance_fields = [
            'jitsi_participant_id', 'jitsi_join_token', 'connection_quality'
        ]
        
        missing_live_class_fields = [field for field in required_live_class_fields if field not in live_classes_columns]
        missing_attendance_fields = [field for field in required_attendance_fields if field not in attendance_columns]
        
        if not missing_live_class_fields and not missing_attendance_fields:
            logger.info("All Jitsi fields already exist. No upgrade needed!")
            return False
            
        logger.info(f"Missing live_class fields: {missing_live_class_fields}")
        logger.info(f"Missing attendance fields: {missing_attendance_fields}")
        return True
    
    def backup_existing_data(self):
        """Backup existing live classes data"""
        logger.info("Backing up existing live classes data...")
        
        try:
            with self.engine.connect() as connection:
                # Check if live_classes table has data
                result = connection.execute(text("SELECT COUNT(*) FROM live_classes"))
                count = result.scalar()
                
                if count > 0:
                    # Create backup table
                    connection.execute(text("""
                        CREATE TABLE IF NOT EXISTS live_classes_backup AS 
                        SELECT * FROM live_classes
                    """))
                    
                    # Create backup for class_attendance
                    connection.execute(text("""
                        CREATE TABLE IF NOT EXISTS class_attendance_backup AS 
                        SELECT * FROM class_attendance
                    """))
                    
                    logger.info(f"Backed up {count} live classes records")
                else:
                    logger.info("No existing live classes data to backup")
                    
        except SQLAlchemyError as e:
            logger.error(f"Error backing up data: {e}")
            return False
            
        return True
    
    def add_jitsi_fields_to_live_classes(self):
        """Add Jitsi Meet specific fields to live_classes table"""
        logger.info("Adding Jitsi fields to live_classes table...")
        
        try:
            with self.engine.connect() as connection:
                trans = connection.begin()
                
                try:
                    # Add Jitsi Meet specific fields
                    jitsi_fields = [
                        ("jitsi_room_name", "VARCHAR(255)"),
                        ("jitsi_meeting_url", "VARCHAR(500)"),
                        ("jitsi_meeting_id", "VARCHAR(255)"),
                        ("jitsi_settings", "TEXT"),  # JSON as TEXT for SQLite
                        ("jitsi_token", "TEXT"),
                        ("description", "TEXT"),
                        ("max_participants", "INTEGER DEFAULT 50"),
                        ("is_password_protected", "BOOLEAN DEFAULT 0"),
                        ("meeting_password", "VARCHAR(100)"),
                        ("allow_join_before_host", "BOOLEAN DEFAULT 1"),
                        ("mute_upon_entry", "BOOLEAN DEFAULT 1"),
                        ("video_off_upon_entry", "BOOLEAN DEFAULT 0"),
                        ("enable_chat", "BOOLEAN DEFAULT 1"),
                        ("enable_whiteboard", "BOOLEAN DEFAULT 1"),
                        ("enable_screen_sharing", "BOOLEAN DEFAULT 1"),
                        ("enable_recording", "BOOLEAN DEFAULT 1"),
                        ("enable_breakout_rooms", "BOOLEAN DEFAULT 1"),
                        ("enable_polls", "BOOLEAN DEFAULT 1"),
                        ("enable_reactions", "BOOLEAN DEFAULT 1")
                    ]
                    
                    existing_columns = self.check_existing_columns('live_classes')
                    
                    for field_name, field_type in jitsi_fields:
                        if field_name not in existing_columns:
                            connection.execute(text(f"ALTER TABLE live_classes ADD COLUMN {field_name} {field_type}"))
                            logger.info(f"Added column: {field_name}")
                        else:
                            logger.info(f"Column already exists: {field_name}")
                    
                    # Create index for jitsi_room_name
                    try:
                        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_live_classes_jitsi_room_name ON live_classes (jitsi_room_name)"))
                        logger.info("Created index for jitsi_room_name")
                    except SQLAlchemyError:
                        logger.info("Index for jitsi_room_name already exists")
                    
                    trans.commit()
                    logger.info("Successfully added Jitsi fields to live_classes table")
                    
                except SQLAlchemyError as e:
                    trans.rollback()
                    logger.error(f"Error adding Jitsi fields: {e}")
                    return False
                    
        except SQLAlchemyError as e:
            logger.error(f"Database connection error: {e}")
            return False
            
        return True
    
    def add_jitsi_fields_to_class_attendance(self):
        """Add Jitsi Meet specific fields to class_attendance table"""
        logger.info("Adding Jitsi fields to class_attendance table...")
        
        try:
            with self.engine.connect() as connection:
                trans = connection.begin()
                
                try:
                    # Add Jitsi Meet specific fields
                    jitsi_attendance_fields = [
                        ("jitsi_participant_id", "VARCHAR(255)"),
                        ("jitsi_join_token", "TEXT"),
                        ("connection_quality", "VARCHAR(50)"),
                        ("device_info", "TEXT")  # JSON as TEXT for SQLite
                    ]
                    
                    existing_columns = self.check_existing_columns('class_attendance')
                    
                    for field_name, field_type in jitsi_attendance_fields:
                        if field_name not in existing_columns:
                            connection.execute(text(f"ALTER TABLE class_attendance ADD COLUMN {field_name} {field_type}"))
                            logger.info(f"Added column: {field_name}")
                        else:
                            logger.info(f"Column already exists: {field_name}")
                    
                    trans.commit()
                    logger.info("Successfully added Jitsi fields to class_attendance table")
                    
                except SQLAlchemyError as e:
                    trans.rollback()
                    logger.error(f"Error adding Jitsi attendance fields: {e}")
                    return False
                    
        except SQLAlchemyError as e:
            logger.error(f"Database connection error: {e}")
            return False
            
        return True
    
    def validate_schema(self):
        """Validate the updated schema"""
        logger.info("Validating updated schema...")
        
        try:
            # Check live_classes table structure
            live_classes_columns = self.check_existing_columns('live_classes')
            required_live_class_fields = [
                'id', 'topic', 'start_time', 'duration', 'status', 'recording_url',
                'jitsi_room_name', 'jitsi_meeting_url', 'jitsi_settings', 'jitsi_token',
                'description', 'max_participants', 'enable_chat', 'enable_whiteboard'
            ]
            
            missing_live_class_fields = [field for field in required_live_class_fields if field not in live_classes_columns]
            
            if missing_live_class_fields:
                logger.error(f"Missing required fields in live_classes: {missing_live_class_fields}")
                return False
            
            # Check class_attendance table structure
            attendance_columns = self.check_existing_columns('class_attendance')
            required_attendance_fields = [
                'id', 'join_time', 'leave_time', 'live_class_id', 'user_id',
                'jitsi_participant_id', 'jitsi_join_token', 'connection_quality'
            ]
            
            missing_attendance_fields = [field for field in required_attendance_fields if field not in attendance_columns]
            
            if missing_attendance_fields:
                logger.error(f"Missing required fields in class_attendance: {missing_attendance_fields}")
                return False
            
            logger.info("Schema validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Schema validation error: {e}")
            return False
    
    def create_sample_data(self):
        """Create sample live class data for testing"""
        logger.info("Creating sample live class data...")
        
        try:
            with self.engine.connect() as connection:
                # Check if we have any users and classes
                user_count = connection.execute(text("SELECT COUNT(*) FROM users")).scalar()
                class_count = connection.execute(text("SELECT COUNT(*) FROM classes")).scalar()
                
                if user_count == 0 or class_count == 0:
                    logger.warning("No users or classes found. Skipping sample data creation.")
                    return True
                
                # Get first teacher and class
                teacher = connection.execute(text("SELECT id FROM users WHERE role = 'teacher' LIMIT 1")).fetchone()
                class_info = connection.execute(text("SELECT id, name FROM classes LIMIT 1")).fetchone()
                
                if not teacher or not class_info:
                    logger.warning("No teacher or class found. Skipping sample data creation.")
                    return True
                
                # Create sample live class
                sample_settings = {
                    "start_with_audio_muted": False,
                    "start_with_video_muted": False,
                    "enable_whiteboard": True,
                    "enable_chat": True,
                    "enable_screen_sharing": True,
                    "enable_recording": True,
                    "enable_breakout_rooms": True,
                    "enable_polls": True,
                    "enable_reactions": True,
                    "max_participants": 50
                }
                
                connection.execute(text("""
                    INSERT INTO live_classes (
                        topic, start_time, duration, status, teacher_id, class_id,
                        jitsi_room_name, jitsi_meeting_url, jitsi_settings, description,
                        max_participants, enable_chat, enable_whiteboard, enable_screen_sharing,
                        enable_recording, enable_breakout_rooms, enable_polls, enable_reactions
                    ) VALUES (
                        'Sample Live Class', 
                        datetime('now', '+1 hour'), 
                        60, 
                        'scheduled', 
                        :teacher_id, 
                        :class_id,
                        'sample-class-room-123',
                        'https://ec2-16-171-4-237.eu-north-1.compute.amazonaws.com:8443/sample-class-room-123',
                        :settings,
                        'This is a sample live class for testing Jitsi integration',
                        50, 1, 1, 1, 1, 1, 1, 1
                    )
                """), {
                    "teacher_id": teacher[0],
                    "class_id": class_info[0],
                    "settings": json.dumps(sample_settings)
                })
                
                logger.info("Created sample live class data")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error creating sample data: {e}")
            return False
    
    def run_upgrade(self):
        """Run the complete upgrade process"""
        logger.info("Starting Live Classes Schema Upgrade...")
        
        try:
            # Step 1: Check existing tables
            if not self.check_existing_tables():
                return False
            
            # Step 2: Check if upgrade is needed
            if not self.check_if_upgrade_needed():
                logger.info("✅ No upgrade needed - all Jitsi fields already exist!")
                return True
            
            # Step 3: Backup existing data
            if not self.backup_existing_data():
                return False
            
            # Step 4: Add Jitsi fields to live_classes
            if not self.add_jitsi_fields_to_live_classes():
                return False
            
            # Step 5: Add Jitsi fields to class_attendance
            if not self.add_jitsi_fields_to_class_attendance():
                return False
            
            # Step 6: Validate schema
            if not self.validate_schema():
                return False
            
            # Step 7: Create sample data (optional)
            if settings.ENVIRONMENT == "development":
                self.create_sample_data()
            
            logger.info("Live Classes Schema Upgrade completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Upgrade failed: {e}")
            return False

def main():
    """Main function to run the upgrade"""
    print("=" * 60)
    print("Live Classes Schema Upgrade Script")
    print("=" * 60)
    
    upgrader = LiveClassesSchemaUpgrader()
    
    if upgrader.run_upgrade():
        print("\n✅ Upgrade completed successfully!")
        print("\nNext steps:")
        print("1. Restart your FastAPI application")
        print("2. Test the live classes functionality")
        print("3. Access Jitsi Meet at: https://ec2-16-171-4-237.eu-north-1.compute.amazonaws.com:8443")
    else:
        print("\n❌ Upgrade failed! Check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
