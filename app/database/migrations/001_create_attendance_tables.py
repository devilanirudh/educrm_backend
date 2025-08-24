"""
Database migration for comprehensive attendance system
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database.session import get_db_url
import logging

logger = logging.getLogger(__name__)

def run_migration():
    """Run the attendance system migration"""
    
    engine = create_engine(get_db_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with engine.connect() as connection:
        try:
            # Start transaction
            trans = connection.begin()
            
            logger.info("Starting attendance system migration...")
            
            # Create attendance_policies table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS attendance_policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    class_id INTEGER,
                    academic_year VARCHAR(20) NOT NULL,
                    school_start_time TIME NOT NULL DEFAULT '08:00:00',
                    school_end_time TIME NOT NULL DEFAULT '15:00:00',
                    late_threshold_minutes INTEGER DEFAULT 15,
                    early_departure_threshold_minutes INTEGER DEFAULT 30,
                    minimum_attendance_percentage FLOAT DEFAULT 75.0,
                    max_consecutive_absences INTEGER DEFAULT 5,
                    max_total_absences INTEGER DEFAULT 30,
                    notify_parents_on_absence BOOLEAN DEFAULT 1,
                    notify_parents_on_late BOOLEAN DEFAULT 0,
                    notify_after_consecutive_absences INTEGER DEFAULT 3,
                    auto_mark_absent_after_minutes INTEGER,
                    allow_self_check_in BOOLEAN DEFAULT 0,
                    allow_self_check_out BOOLEAN DEFAULT 0,
                    grace_period_minutes INTEGER DEFAULT 5,
                    half_day_threshold_hours FLOAT DEFAULT 4.0,
                    working_days TEXT DEFAULT '["monday", "tuesday", "wednesday", "thursday", "friday"]',
                    is_active BOOLEAN DEFAULT 1 NOT NULL,
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (class_id) REFERENCES classes (id),
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """))
            
            # Create attendance_sessions table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS attendance_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_id INTEGER NOT NULL,
                    subject_id INTEGER,
                    session_name VARCHAR(100) NOT NULL,
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL,
                    late_threshold_minutes INTEGER DEFAULT 5,
                    is_required BOOLEAN DEFAULT 1,
                    weight FLOAT DEFAULT 1.0,
                    is_active BOOLEAN DEFAULT 1 NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (class_id) REFERENCES classes (id),
                    FOREIGN KEY (subject_id) REFERENCES subjects (id)
                )
            """))
            
            # Create period_attendance table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS period_attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    session_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'absent',
                    check_in_time TIMESTAMP,
                    check_out_time TIMESTAMP,
                    reason TEXT,
                    notes TEXT,
                    marked_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES students (id),
                    FOREIGN KEY (session_id) REFERENCES attendance_sessions (id),
                    FOREIGN KEY (marked_by) REFERENCES users (id)
                )
            """))
            
            # Create attendance_exceptions table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS attendance_exceptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    exception_type VARCHAR(50) NOT NULL,
                    reason TEXT NOT NULL,
                    approved_by INTEGER NOT NULL,
                    mark_as_present BOOLEAN DEFAULT 0,
                    exclude_from_calculation BOOLEAN DEFAULT 1,
                    is_active BOOLEAN DEFAULT 1 NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES students (id),
                    FOREIGN KEY (approved_by) REFERENCES users (id)
                )
            """))
            
            # Create attendance_notifications table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS attendance_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    notification_type VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    message TEXT NOT NULL,
                    date DATE NOT NULL,
                    sent_to_parents BOOLEAN DEFAULT 0,
                    sent_to_teachers BOOLEAN DEFAULT 0,
                    sent_to_admin BOOLEAN DEFAULT 0,
                    is_sent BOOLEAN DEFAULT 0 NOT NULL,
                    sent_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES students (id)
                )
            """))
            
            # Update existing attendance_records table with new columns
            try:
                # Add new columns to existing attendance_records table
                connection.execute(text("""
                    ALTER TABLE attendance_records 
                    ADD COLUMN policy_id INTEGER REFERENCES attendance_policies (id)
                """))
            except Exception as e:
                logger.info("Column policy_id might already exist: %s", str(e))
            
            try:
                connection.execute(text("""
                    ALTER TABLE attendance_records 
                    ADD COLUMN attendance_type VARCHAR(20) DEFAULT 'daily'
                """))
            except Exception as e:
                logger.info("Column attendance_type might already exist: %s", str(e))
            
            try:
                connection.execute(text("""
                    ALTER TABLE attendance_records 
                    ADD COLUMN expected_check_in TIME
                """))
            except Exception as e:
                logger.info("Column expected_check_in might already exist: %s", str(e))
            
            try:
                connection.execute(text("""
                    ALTER TABLE attendance_records 
                    ADD COLUMN expected_check_out TIME
                """))
            except Exception as e:
                logger.info("Column expected_check_out might already exist: %s", str(e))
            
            try:
                connection.execute(text("""
                    ALTER TABLE attendance_records 
                    ADD COLUMN actual_check_in TIMESTAMP
                """))
            except Exception as e:
                logger.info("Column actual_check_in might already exist: %s", str(e))
            
            try:
                connection.execute(text("""
                    ALTER TABLE attendance_records 
                    ADD COLUMN actual_check_out TIMESTAMP
                """))
            except Exception as e:
                logger.info("Column actual_check_out might already exist: %s", str(e))
            
            try:
                connection.execute(text("""
                    ALTER TABLE attendance_records 
                    ADD COLUMN total_hours FLOAT
                """))
            except Exception as e:
                logger.info("Column total_hours might already exist: %s", str(e))
            
            try:
                connection.execute(text("""
                    ALTER TABLE attendance_records 
                    ADD COLUMN expected_hours FLOAT
                """))
            except Exception as e:
                logger.info("Column expected_hours might already exist: %s", str(e))
            
            try:
                connection.execute(text("""
                    ALTER TABLE attendance_records 
                    ADD COLUMN check_in_location TEXT
                """))
            except Exception as e:
                logger.info("Column check_in_location might already exist: %s", str(e))
            
            try:
                connection.execute(text("""
                    ALTER TABLE attendance_records 
                    ADD COLUMN check_out_location TEXT
                """))
            except Exception as e:
                logger.info("Column check_out_location might already exist: %s", str(e))
            
            try:
                connection.execute(text("""
                    ALTER TABLE attendance_records 
                    ADD COLUMN check_in_device VARCHAR(100)
                """))
            except Exception as e:
                logger.info("Column check_in_device might already exist: %s", str(e))
            
            try:
                connection.execute(text("""
                    ALTER TABLE attendance_records 
                    ADD COLUMN check_out_device VARCHAR(100)
                """))
            except Exception as e:
                logger.info("Column check_out_device might already exist: %s", str(e))
            
            try:
                connection.execute(text("""
                    ALTER TABLE attendance_records 
                    ADD COLUMN notes TEXT
                """))
            except Exception as e:
                logger.info("Column notes might already exist: %s", str(e))
            
            try:
                connection.execute(text("""
                    ALTER TABLE attendance_records 
                    ADD COLUMN is_verified BOOLEAN DEFAULT 0 NOT NULL
                """))
            except Exception as e:
                logger.info("Column is_verified might already exist: %s", str(e))
            
            try:
                connection.execute(text("""
                    ALTER TABLE attendance_records 
                    ADD COLUMN verified_by INTEGER REFERENCES users (id)
                """))
            except Exception as e:
                logger.info("Column verified_by might already exist: %s", str(e))
            
            try:
                connection.execute(text("""
                    ALTER TABLE attendance_records 
                    ADD COLUMN verified_at TIMESTAMP
                """))
            except Exception as e:
                logger.info("Column verified_at might already exist: %s", str(e))
            
            # Create indexes for better performance
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_attendance_records_student_date 
                ON attendance_records (student_id, date)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_attendance_records_class_date 
                ON attendance_records (class_id, date)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_attendance_records_status 
                ON attendance_records (status)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_attendance_policies_class 
                ON attendance_policies (class_id)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_attendance_sessions_class 
                ON attendance_sessions (class_id)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_period_attendance_student_session 
                ON period_attendance (student_id, session_id, date)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_attendance_exceptions_student_date 
                ON attendance_exceptions (student_id, date)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_attendance_notifications_student 
                ON attendance_notifications (student_id, date)
            """))
            
            # Insert default global attendance policy
            connection.execute(text("""
                INSERT OR IGNORE INTO attendance_policies (
                    name, description, academic_year, school_start_time, school_end_time,
                    minimum_attendance_percentage, created_by
                ) VALUES (
                    'Default Global Policy',
                    'Default attendance policy for all classes',
                    '2024-2025',
                    '08:00:00',
                    '15:00:00',
                    75.0,
                    1
                )
            """))
            
            # Commit transaction
            trans.commit()
            
            logger.info("Attendance system migration completed successfully!")
            
        except Exception as e:
            # Rollback transaction on error
            trans.rollback()
            logger.error("Migration failed: %s", str(e))
            raise e

if __name__ == "__main__":
    run_migration()
