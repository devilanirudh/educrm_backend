"""
Configuration settings for the E-School Management Platform
"""

from typing import List, Optional, Union
from pydantic import EmailStr, validator
from pydantic_settings import BaseSettings
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # Project Information
    PROJECT_NAME: str = "E-School Management Platform"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Unified E-Learning, CMS, and CRM Platform for K-12 Institutions"
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8
    
    # Database
    DATABASE_URL: str = "duckdb:///./eschool.db"
    DATABASE_ECHO: bool = False  # Set to True for SQL query logging
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React development server
        "http://localhost:3001",  # Alternative React port
        "http://127.0.0.1:3000",
        "https://educrm-frontend.vercel.app",  # Vercel frontend
        "https://educrm-frontend-git-main.vercel.app",  # Vercel preview deployments
        "https://*.vercel.app",  # All Vercel subdomains
    ]
    
    # Trusted Hosts (for production)
    ALLOWED_HOSTS: List[str] = [
        "localhost", 
        "127.0.0.1",
        "educrmbackend-production.up.railway.app",
        "educrm-frontend.vercel.app",
        "*.vercel.app"
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Email Configuration
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    @validator("EMAILS_FROM_NAME")
    def get_project_name(cls, v: Optional[str], values: dict[str, any]) -> str:
        if not v:
            return values["PROJECT_NAME"]
        return v
    
    # File Upload Configuration
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    ALLOWED_DOCUMENT_TYPES: List[str] = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
        "text/csv"
    ]
    ALLOWED_VIDEO_TYPES: List[str] = [
        "video/mp4",
        "video/mpeg",
        "video/quicktime",
        "video/x-msvideo"
    ]
    
    # Redis Configuration (for caching and sessions)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # Payment Gateway Configuration
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # SMS Configuration (Twilio)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # Push Notification Configuration
    FCM_SERVER_KEY: Optional[str] = None
    
    # Live Classes Configuration
    JITSI_MEET_DOMAIN: str = "meet.jit.si"
    JITSI_MEET_APP_ID: Optional[str] = None
    JITSI_MEET_SECRET: Optional[str] = None
    
    # School Configuration
    SCHOOL_NAME: str = "Demo School"
    SCHOOL_ADDRESS: str = "123 Education Street"
    SCHOOL_PHONE: str = "+1-234-567-8900"
    SCHOOL_EMAIL: EmailStr = "info@demoschool.edu"
    SCHOOL_WEBSITE: str = "https://demoschool.edu"
    SCHOOL_LOGO_URL: Optional[str] = None
    
    # Academic Year Configuration
    ACADEMIC_YEAR_START_MONTH: int = 9  # September
    ACADEMIC_YEAR_END_MONTH: int = 6    # June
    
    # Grading System Configuration
    GRADING_SCALE: dict = {
        "A": {"min": 90, "max": 100, "points": 4.0},
        "B": {"min": 80, "max": 89, "points": 3.0},
        "C": {"min": 70, "max": 79, "points": 2.0},
        "D": {"min": 60, "max": 69, "points": 1.0},
        "F": {"min": 0, "max": 59, "points": 0.0}
    }
    
    # Attendance Configuration
    ATTENDANCE_GRACE_MINUTES: int = 15  # Late arrival grace period
    MINIMUM_ATTENDANCE_PERCENTAGE: float = 75.0  # Minimum required attendance
    
    # Notification Configuration
    MAX_NOTIFICATIONS_PER_USER: int = 100
    NOTIFICATION_RETENTION_DAYS: int = 30
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 100
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    # Backup Configuration
    BACKUP_ENABLED: bool = True
    BACKUP_SCHEDULE: str = "0 2 * * *"  # Daily at 2 AM (cron format)
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_LOCATION: str = "./backups"
    
    # Analytics Configuration
    ANALYTICS_ENABLED: bool = True
    ANALYTICS_RETENTION_MONTHS: int = 24
    
    # Default Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Time Zone
    TIMEZONE: str = "UTC"
    
    # Language and Localization
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: List[str] = ["en", "es", "fr", "de", "it"]
    
    # Feature Flags
    ENABLE_LIVE_CLASSES: bool = True
    ENABLE_ONLINE_PAYMENTS: bool = True
    ENABLE_SMS_NOTIFICATIONS: bool = True
    ENABLE_EMAIL_NOTIFICATIONS: bool = True
    ENABLE_PUSH_NOTIFICATIONS: bool = True
    ENABLE_FILE_UPLOADS: bool = True
    ENABLE_ADVANCED_ANALYTICS: bool = True
    ENABLE_API_RATE_LIMITING: bool = True
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create global settings instance
settings = Settings()

# Ensure upload directory exists
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
