# E-School Management Platform - API Documentation

## Overview

The E-School Management Platform provides a comprehensive RESTful API built with FastAPI. This API serves as the backend for the unified school management system that integrates E-Learning, CMS, and CRM functionalities.

## Base URL

- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://your-domain.com/api/v1`

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Authentication Endpoints

#### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin@school.edu&password=admin123
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "admin@school.edu",
    "first_name": "System",
    "last_name": "Administrator",
    "role": "admin",
    "is_verified": true
  }
}
```

#### Get Current User
```http
GET /auth/me
Authorization: Bearer <token>
```

#### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Logout
```http
POST /auth/logout
Authorization: Bearer <token>
```

## Core Modules

### Student Management

#### List Students
```http
GET /students?page=1&per_page=20&search=john
Authorization: Bearer <token>
```

#### Get Student
```http
GET /students/{student_id}
Authorization: Bearer <token>
```

#### Create Student
```http
POST /students
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "student@school.edu",
  "first_name": "John",
  "last_name": "Doe",
  "student_id": "STU001",
  "admission_date": "2024-08-01",
  "current_class_id": 1,
  "academic_year": "2024-2025"
}
```

#### Update Student
```http
PUT /students/{student_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "Updated Name",
  "phone": "+1234567890"
}
```

### Teacher Management

#### List Teachers
```http
GET /teachers?page=1&per_page=20
Authorization: Bearer <token>
```

#### Get Teacher
```http
GET /teachers/{teacher_id}
Authorization: Bearer <token>
```

#### Create Teacher
```http
POST /teachers
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "teacher@school.edu",
  "first_name": "Jane",
  "last_name": "Smith",
  "employee_id": "EMP001",
  "qualification": "M.Sc. Mathematics",
  "joining_date": "2020-08-01",
  "employment_type": "permanent"
}
```

### Class Management

#### List Classes
```http
GET /classes
Authorization: Bearer <token>
```

#### Create Class
```http
POST /classes
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Grade 1",
  "section": "A",
  "grade_level": 1,
  "academic_year": "2024-2025",
  "capacity": 30,
  "class_teacher_id": 1
}
```

### Assignment Management

#### List Assignments
```http
GET /assignments?class_id=1&subject_id=1
Authorization: Bearer <token>
```

#### Create Assignment
```http
POST /assignments
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Mathematics Homework",
  "description": "Complete exercises 1-10",
  "class_id": 1,
  "subject_id": 1,
  "assigned_date": "2024-01-15T09:00:00Z",
  "due_date": "2024-01-20T23:59:59Z",
  "max_score": 100.0
}
```

#### Submit Assignment
```http
POST /assignments/{assignment_id}/submit
Authorization: Bearer <token>
Content-Type: multipart/form-data

student_id=1&submission_text=My solution&file=@homework.pdf
```

### Exam Management

#### List Exams
```http
GET /exams?class_id=1&subject_id=1
Authorization: Bearer <token>
```

#### Create Exam
```http
POST /exams
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Mid-term Mathematics Exam",
  "class_id": 1,
  "subject_id": 1,
  "exam_date": "2024-02-15T10:00:00Z",
  "duration_minutes": 120,
  "max_score": 100.0,
  "exam_type": "mid_term"
}
```

### Fee Management

#### List Fee Structures
```http
GET /fees/structures
Authorization: Bearer <token>
```

#### Create Payment
```http
POST /fees/payments
Authorization: Bearer <token>
Content-Type: application/json

{
  "student_id": 1,
  "fee_structure_id": 1,
  "amount": 500.00,
  "payment_method": "online",
  "payment_date": "2024-01-15"
}
```

### Live Classes

#### List Live Classes
```http
GET /live-classes?class_id=1&date=2024-01-15
Authorization: Bearer <token>
```

#### Create Live Class
```http
POST /live-classes
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Mathematics Class",
  "class_id": 1,
  "subject_id": 1,
  "scheduled_start": "2024-01-15T10:00:00Z",
  "scheduled_end": "2024-01-15T11:00:00Z",
  "meeting_link": "https://meet.jit.si/math-class-123"
}
```

### Library Management

#### List Books
```http
GET /library/books?search=mathematics&category=textbook
Authorization: Bearer <token>
```

#### Borrow Book
```http
POST /library/transactions
Authorization: Bearer <token>
Content-Type: application/json

{
  "book_id": 1,
  "student_id": 1,
  "issue_date": "2024-01-15",
  "due_date": "2024-01-29"
}
```

### Communication

#### Send Notification
```http
POST /communication/notifications
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": 1,
  "title": "Assignment Due Reminder",
  "message": "Your mathematics assignment is due tomorrow",
  "notification_type": "reminder",
  "channels": ["web", "email"]
}
```

#### List Messages
```http
GET /communication/messages?user_id=1
Authorization: Bearer <token>
```

### CMS (Content Management)

#### List Pages
```http
GET /cms/pages?status=published
Authorization: Bearer <token>
```

#### Create Page
```http
POST /cms/pages
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "About Us",
  "slug": "about-us",
  "content": "<h1>About Our School</h1><p>Welcome to our institution...</p>",
  "page_type": "page",
  "is_published": true
}
```

#### List News Articles
```http
GET /cms/news?category=academic&limit=10
Authorization: Bearer <token>
```

### CRM (Customer Relationship Management)

#### List Leads
```http
GET /crm/leads?status=new&assigned_to=1
Authorization: Bearer <token>
```

#### Create Lead
```http
POST /crm/leads
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@email.com",
  "phone": "+1234567890",
  "source": "website",
  "status": "new",
  "grade_interested": "Grade 1"
}
```

### Reports & Analytics

#### Get Dashboard Stats
```http
GET /reports/dashboard-stats
Authorization: Bearer <token>
```

#### Generate Report
```http
POST /reports/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "report_type": "student_performance",
  "class_id": 1,
  "date_from": "2024-01-01",
  "date_to": "2024-01-31",
  "format": "pdf"
}
```

## Error Handling

The API uses standard HTTP status codes:

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

Error response format:
```json
{
  "detail": "Error message",
  "errors": {
    "field_name": ["Validation error message"]
  }
}
```

## Pagination

List endpoints support pagination:

```http
GET /students?page=1&per_page=20&sort_by=created_at&sort_order=desc
```

Response includes pagination metadata:
```json
{
  "data": [...],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "pages": 8,
  "has_next": true,
  "has_prev": false
}
```

## Rate Limiting

API requests are rate-limited:
- 60 requests per minute per user
- 100 requests burst limit

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1609459200
```

## Webhooks

The platform supports webhooks for real-time notifications:

### Available Events
- `student.created`
- `student.updated`
- `grade.created`
- `payment.completed`
- `assignment.submitted`

### Webhook Payload
```json
{
  "event": "student.created",
  "data": {
    "id": 1,
    "student_id": "STU001",
    "first_name": "John",
    "last_name": "Doe"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## SDKs and Libraries

- **Python**: `pip install eschool-python-sdk`
- **JavaScript**: `npm install eschool-js-sdk`
- **PHP**: `composer require eschool/php-sdk`

## Support

- **Documentation**: https://docs.eschool.com
- **Support Email**: support@eschool.com
- **GitHub Issues**: https://github.com/eschool/platform/issues
