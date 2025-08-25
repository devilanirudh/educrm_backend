#!/usr/bin/env python3
"""
Migration script to add impersonation fields to UserSession table
"""

import sqlite3
import os
from datetime import datetime

def migrate_impersonation():
    """Add impersonation fields to UserSession table"""
    
    # Database path
    db_path = "eschool.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Checking current UserSession table structure...")
        
        # Check if impersonation fields already exist
        cursor.execute("PRAGMA table_info(user_sessions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📋 Current columns: {columns}")
        
        # Add impersonation fields if they don't exist
        if 'impersonated_by' not in columns:
            print("➕ Adding impersonated_by column...")
            cursor.execute("""
                ALTER TABLE user_sessions 
                ADD COLUMN impersonated_by INTEGER 
                REFERENCES users(id)
            """)
            print("✅ Added impersonated_by column")
        
        if 'is_impersonation' not in columns:
            print("➕ Adding is_impersonation column...")
            cursor.execute("""
                ALTER TABLE user_sessions 
                ADD COLUMN is_impersonation BOOLEAN 
                DEFAULT FALSE
            """)
            print("✅ Added is_impersonation column")
        
        # Commit changes
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(user_sessions)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Updated columns: {new_columns}")
        
        print("✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Starting impersonation migration...")
    success = migrate_impersonation()
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
        exit(1)
