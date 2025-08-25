#!/usr/bin/env python3
"""
Cleanup script to remove old impersonation sessions with wrong token format
"""

import sqlite3
import os

def cleanup_old_sessions():
    """Remove old impersonation sessions with wrong token format"""
    
    # Database path
    db_path = "eschool.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Checking for old impersonation sessions...")
        
        # Find sessions with wrong token format
        cursor.execute("""
            SELECT id, session_token, user_id, created_at 
            FROM user_sessions 
            WHERE is_impersonation = 1 AND session_token = 'impersonation_session'
        """)
        
        old_sessions = cursor.fetchall()
        
        if old_sessions:
            print(f"🗑️ Found {len(old_sessions)} old sessions to clean up:")
            for session in old_sessions:
                print(f"  - Session {session[0]}: token={session[1]}, user_id={session[2]}, created={session[3]}")
            
            # Delete old sessions
            cursor.execute("""
                DELETE FROM user_sessions 
                WHERE is_impersonation = 1 AND session_token = 'impersonation_session'
            """)
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"✅ Deleted {deleted_count} old sessions")
        else:
            print("✅ No old sessions found to clean up")
        
        # Show remaining sessions
        cursor.execute("""
            SELECT id, session_token, user_id, created_at 
            FROM user_sessions 
            WHERE is_impersonation = 1
        """)
        
        remaining_sessions = cursor.fetchall()
        print(f"📋 Remaining impersonation sessions: {len(remaining_sessions)}")
        for session in remaining_sessions:
            print(f"  - Session {session[0]}: token={session[1][:20]}..., user_id={session[2]}, created={session[3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {str(e)}")
        return False
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Starting session cleanup...")
    success = cleanup_old_sessions()
    if success:
        print("🎉 Cleanup completed successfully!")
    else:
        print("💥 Cleanup failed!")
        exit(1)
