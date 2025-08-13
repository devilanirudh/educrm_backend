"""
E-School Management Platform - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import os
import sys
from pathlib import Path

from app.core.config import settings
from app.database.session import engine
from app.database.init_db import init_db
from app.api.v1 import auth, students, teachers, classes, assignments, exams, fees, live_classes
from app.api.v1 import library, transport, hostel, events, cms, crm, reports, communication

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    E-School Management Platform API
    
    A comprehensive, unified web application that seamlessly integrates:
    - E-Learning Management System (LMS)
    - Content Management System (CMS) 
    - Customer Relationship Management (CRM)
    
    This platform centralizes academic, administrative, communication, and online learning 
    processes for K-12 institutions.
    """,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS] if settings.BACKEND_CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Create upload directory if it doesn't exist
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include API routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(students.router, prefix=f"{settings.API_V1_STR}/students", tags=["Student Management"])
app.include_router(teachers.router, prefix=f"{settings.API_V1_STR}/teachers", tags=["Teacher Management"])
app.include_router(classes.router, prefix=f"{settings.API_V1_STR}/classes", tags=["Class Management"])
app.include_router(assignments.router, prefix=f"{settings.API_V1_STR}/assignments", tags=["Assignments"])
app.include_router(exams.router, prefix=f"{settings.API_V1_STR}/exams", tags=["Exams"])
app.include_router(fees.router, prefix=f"{settings.API_V1_STR}/fees", tags=["Fees & Payments"])
app.include_router(live_classes.router, prefix=f"{settings.API_V1_STR}/live-classes", tags=["Live Classes"])
app.include_router(library.router, prefix=f"{settings.API_V1_STR}/library", tags=["Library"])
app.include_router(transport.router, prefix=f"{settings.API_V1_STR}/transport", tags=["Transport"])
app.include_router(hostel.router, prefix=f"{settings.API_V1_STR}/hostel", tags=["Hostel"])
app.include_router(events.router, prefix=f"{settings.API_V1_STR}/events", tags=["Events"])
app.include_router(cms.router, prefix=f"{settings.API_V1_STR}/cms", tags=["Content Management"])
app.include_router(crm.router, prefix=f"{settings.API_V1_STR}/crm", tags=["Customer Relationship Management"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["Reports & Analytics"])
app.include_router(communication.router, prefix=f"{settings.API_V1_STR}/communication", tags=["Communication"])

@app.on_event("startup")
async def startup_event():
    """Initialize the database on startup"""
    init_db()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    if hasattr(engine, 'dispose'):
        engine.dispose()

@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "E-School Management Platform API",
        "version": settings.VERSION,
        "status": "healthy",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database": "connected",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Resource not found",
            "path": str(request.url.path),
            "method": request.method
        }
    )

@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    """Custom 500 handler"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )

if __name__ == "__main__":
    print("⚠️  Warning: Running main.py directly is not recommended.")
    print("🔧 Please run the server using one of these methods:")
    print("   1. From backend directory: python run_server.py")
    print("   2. From backend directory: uvicorn app.main:app --reload")
    print("   3. From backend directory: python -m uvicorn app.main:app --reload")
    print()
    
    # Still allow direct execution for convenience
    uvicorn.run(
        "app.main:app" if "app" in sys.modules else "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )
