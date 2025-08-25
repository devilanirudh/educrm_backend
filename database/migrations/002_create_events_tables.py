"""
Migration: Create events tables
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from app.database.session import engine
from app.models.events import Event, EventAssignment

def upgrade():
    """Create events tables"""
    # Create tables
    Event.__table__.create(engine, checkfirst=True)
    EventAssignment.__table__.create(engine, checkfirst=True)
    
    print("✅ Events tables created successfully")

def downgrade():
    """Drop events tables"""
    EventAssignment.__table__.drop(engine, checkfirst=True)
    Event.__table__.drop(engine, checkfirst=True)
    
    print("✅ Events tables dropped successfully")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
