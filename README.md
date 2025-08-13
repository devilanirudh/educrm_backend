# E-School Management Platform - Backend

This is the backend API for the E-School Management Platform, built with FastAPI and DuckDB.

## Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs with Python
- **DuckDB**: High-performance analytical database engine
- **SQLAlchemy**: Database ORM for Python
- **Pydantic**: Data validation using Python type annotations
- **JWT**: JSON Web Tokens for authentication
- **bcrypt**: Password hashing
- **Uvicorn**: ASGI server implementation

## Project Structure

```
backend/
├── app/
│   ├── api/                # API routes and endpoints
│   │   ├── v1/            # API version 1
│   │   │   ├── auth.py    # Authentication endpoints
│   │   │   ├── students.py # Student management
│   │   │   ├── teachers.py # Teacher management
│   │   │   ├── classes.py  # Class management
│   │   │   ├── assignments.py # Assignment management
│   │   │   ├── exams.py    # Exam management
│   │   │   ├── fees.py     # Fee management
│   │   │   ├── live_classes.py # Live class management
│   │   │   ├── library.py  # Library management
│   │   │   ├── transport.py # Transport management
│   │   │   ├── hostel.py   # Hostel management
│   │   │   ├── events.py   # Event management
│   │   │   ├── cms.py      # Content Management System
│   │   │   ├── crm.py      # Customer Relationship Management
│   │   │   ├── reports.py  # Reports and Analytics
│   │   │   └── communication.py # Communication system
│   │   └── deps.py        # Dependency injection
│   ├── core/              # Core functionality
│   │   ├── config.py      # Configuration settings
│   │   ├── security.py    # Security utilities
│   │   └── permissions.py # Role-based permissions
│   ├── database/          # Database configuration
│   │   ├── init_db.py     # Database initialization
│   │   └── session.py     # Database session management
│   ├── models/            # SQLAlchemy models
│   │   ├── user.py        # User models
│   │   ├── student.py     # Student models
│   │   ├── teacher.py     # Teacher models
│   │   ├── academic.py    # Academic models
│   │   ├── financial.py   # Financial models
│   │   ├── content.py     # Content models
│   │   └── communication.py # Communication models
│   ├── schemas/           # Pydantic schemas
│   │   ├── user.py        # User schemas
│   │   ├── student.py     # Student schemas
│   │   ├── teacher.py     # Teacher schemas
│   │   ├── academic.py    # Academic schemas
│   │   ├── financial.py   # Financial schemas
│   │   ├── content.py     # Content schemas
│   │   └── communication.py # Communication schemas
│   ├── services/          # Business logic
│   │   ├── auth.py        # Authentication service
│   │   ├── student.py     # Student service
│   │   ├── teacher.py     # Teacher service
│   │   ├── academic.py    # Academic service
│   │   ├── financial.py   # Financial service
│   │   ├── content.py     # Content service
│   │   ├── communication.py # Communication service
│   │   └── notification.py # Notification service
│   ├── utils/             # Utility functions
│   │   ├── date.py        # Date utilities
│   │   ├── email.py       # Email utilities
│   │   ├── file.py        # File utilities
│   │   └── validators.py  # Custom validators
│   └── main.py            # FastAPI application entry point
├── docs/                  # Documentation
│   ├── api.md             # API documentation
│   ├── database.md        # Database schema documentation
│   ├── deployment.md      # Deployment guide
│   └── development.md     # Development guide
├── tests/                 # Test files
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Features

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- Password hashing with bcrypt
- OAuth integration support

### Core Modules
- **Student Management**: Complete student lifecycle management
- **Teacher Management**: Faculty administration and scheduling
- **Academic Management**: Classes, assignments, exams, and grading
- **Financial Management**: Fees, payments, and billing
- **Content Management**: Website content and learning resources
- **Communication**: Multi-channel messaging and notifications

### Database Features
- High-performance DuckDB for analytics
- Optimized queries for reporting
- Automatic data archiving
- Backup and recovery

### API Features
- RESTful API design
- Automatic API documentation with Swagger/OpenAPI
- Request/response validation
- Error handling and logging
- Rate limiting
- CORS support

## Setup and Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the backend directory:
   ```bash
   # Database
   DATABASE_URL=duckdb:///./eschool.db
   
   # Security
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # CORS
   BACKEND_CORS_ORIGINS=["http://localhost:3000"]
   
   # Email Configuration
   SMTP_TLS=True
   SMTP_PORT=587
   SMTP_HOST=smtp.gmail.com
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-password
   
   # File Upload
   UPLOAD_DIR=./uploads
   MAX_FILE_SIZE=10485760  # 10MB
   
   # Redis (for caching and sessions)
   REDIS_URL=redis://localhost:6379
   ```

5. **Initialize the database**:
   ```bash
   python -m app.database.init_db
   ```

6. **Run the application**:
   
   **Option 1: Using the startup script (Recommended)**
   ```bash
   ./start.sh
   ```
   
   **Option 2: Using the Python runner**
   ```bash
   python run_server.py
   ```
   
   **Option 3: Using uvicorn directly**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   
   **⚠️ Important**: Make sure to run these commands from the `backend/` directory, not from `backend/app/`

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, you can access:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Development

### Code Style
- Follow PEP 8 conventions
- Use type hints for all functions
- Write docstrings for all public functions and classes

### Testing
Run tests with pytest:
```bash
pytest
```

### Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head
```

### Adding New Endpoints

1. Create the Pydantic schema in `schemas/`
2. Create the SQLAlchemy model in `models/`
3. Implement business logic in `services/`
4. Create the API endpoint in `api/v1/`
5. Add tests in `tests/`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | DuckDB database URL | `duckdb:///./eschool.db` |
| `SECRET_KEY` | JWT secret key | Required |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration | `30` |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins | `[]` |
| `SMTP_HOST` | Email SMTP host | Required for email |
| `SMTP_PORT` | Email SMTP port | `587` |
| `SMTP_USER` | Email username | Required for email |
| `SMTP_PASSWORD` | Email password | Required for email |
| `UPLOAD_DIR` | File upload directory | `./uploads` |
| `MAX_FILE_SIZE` | Maximum file size in bytes | `10485760` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |

## Deployment

### Docker
```bash
# Build the Docker image
docker build -t eschool-backend .

# Run the container
docker run -p 8000:8000 eschool-backend
```

### Production Considerations
- Use a production ASGI server like Gunicorn with Uvicorn workers
- Set up proper logging configuration
- Configure environment-specific settings
- Set up database backups
- Implement monitoring and health checks
- Use HTTPS in production
- Configure rate limiting
- Set up proper error tracking

## Security

### Authentication Flow
1. User submits credentials to `/auth/login`
2. Server validates credentials and returns JWT token
3. Client includes token in `Authorization: Bearer <token>` header
4. Server validates token and extracts user information
5. User permissions are checked based on role

### Security Features
- Password hashing with bcrypt
- JWT token expiration
- Role-based permissions
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CORS configuration
- Rate limiting

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `POST /auth/refresh` - Refresh token
- `GET /auth/me` - Get current user
- `POST /auth/forgot-password` - Password reset request
- `POST /auth/reset-password` - Reset password

### Student Management
- `GET /students` - List students
- `POST /students` - Create student
- `GET /students/{id}` - Get student details
- `PUT /students/{id}` - Update student
- `DELETE /students/{id}` - Delete student
- `GET /students/{id}/grades` - Get student grades
- `GET /students/{id}/attendance` - Get attendance records

### Teacher Management
- `GET /teachers` - List teachers
- `POST /teachers` - Create teacher
- `GET /teachers/{id}` - Get teacher details
- `PUT /teachers/{id}` - Update teacher
- `DELETE /teachers/{id}` - Delete teacher
- `GET /teachers/{id}/classes` - Get assigned classes
- `GET /teachers/{id}/schedule` - Get teaching schedule

### Academic Management
- `GET /classes` - List classes
- `POST /classes` - Create class
- `GET /assignments` - List assignments
- `POST /assignments` - Create assignment
- `GET /exams` - List exams
- `POST /exams` - Create exam

### Financial Management
- `GET /fees` - List fee structures
- `POST /fees` - Create fee structure
- `GET /payments` - List payments
- `POST /payments` - Process payment
- `GET /invoices` - List invoices

### Content Management
- `GET /cms/pages` - List CMS pages
- `POST /cms/pages` - Create page
- `GET /cms/news` - List news articles
- `POST /cms/news` - Create news article
- `GET /cms/media` - List media files
- `POST /cms/media` - Upload media

### Communication
- `GET /notifications` - List notifications
- `POST /notifications` - Send notification
- `GET /messages` - List messages
- `POST /messages` - Send message

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is proprietary software for educational institutions.
# educrm_backend
