#!/usr/bin/env python3
"""
Startup script for E-School Management Platform Backend
Run this script from the backend directory to start the server
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import uvicorn
from app.core.config import settings

def main():
    """Main entry point for running the FastAPI server"""
    print("🚀 Starting E-School Management Platform Backend...")
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    print(f"🔗 Server URL: http://localhost:{settings.PORT}")
    print(f"📚 API Docs: http://localhost:{settings.PORT}/docs")
    print(f"📖 ReDoc: http://localhost:{settings.PORT}/redoc")
    print("-" * 50)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
        access_log=True
    )

if __name__ == "__main__":
    main()
