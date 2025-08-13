"""
Database session management for DuckDB
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.core.config import settings
import duckdb
import sqlite3
from pathlib import Path

# For now, we'll use SQLite as DuckDB's SQLAlchemy dialect has some compatibility issues
# We'll switch to DuckDB for analytics queries while using SQLite for ORM operations
database_path = settings.DATABASE_URL.replace("duckdb:///", "").replace("sqlite:///", "")
if not database_path.startswith("./"):
    database_path = f"./{database_path}"

# Create SQLite engine for ORM operations (more stable)
sqlite_url = f"sqlite:///{database_path}"
engine = create_engine(
    sqlite_url,
    echo=settings.DATABASE_ECHO,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
    }
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()

def get_db() -> Session:
    """
    Dependency function to get database session
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_connection():
    """
    Get raw DuckDB connection for analytics queries
    
    Returns:
        DuckDB connection
    """
    # Create a DuckDB connection that can read from SQLite
    duck_conn = duckdb.connect()
    duck_conn.execute(f"ATTACH '{database_path}' AS sqlite_db (TYPE sqlite)")
    return duck_conn

def get_sqlite_connection():
    """
    Get raw SQLite connection for direct queries
    
    Returns:
        SQLite connection
    """
    return sqlite3.connect(database_path)

async def get_async_db() -> Session:
    """
    Async version of get_db for async endpoints
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Create all database tables
    """
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """
    Drop all database tables (use with caution!)
    """
    Base.metadata.drop_all(bind=engine)
