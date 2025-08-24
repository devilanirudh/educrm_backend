#!/usr/bin/env python3
"""
Migration script to add Firebase UID column to users table
"""
from app.database.session import engine
from sqlalchemy import text

def migrate_firebase_uid():
    """Add firebase_uid column to users table"""
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT COUNT(*) FROM pragma_table_info('users') 
                WHERE name = 'firebase_uid'
            """))
            column_exists = result.scalar() > 0
            
            if not column_exists:
                # Add the column
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN firebase_uid VARCHAR(128) UNIQUE
                """))
                conn.commit()
                print("✅ Added firebase_uid column to users table")
            else:
                print("ℹ️ firebase_uid column already exists")
                
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    migrate_firebase_uid()
