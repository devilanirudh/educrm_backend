# E-School Management Platform - Database Schema Documentation

## Overview

The E-School Management Platform uses DuckDB as its primary database engine. DuckDB is chosen for its excellent analytical capabilities, which are essential for generating reports and performing complex queries on educational data.

## Database Architecture

### Key Design Principles

1. **Single Source of Truth**: All data is centralized in one unified schema
2. **ACID Compliance**: Ensures data integrity and consistency
3. **Scalability**: Designed to handle growing student populations
4. **Performance**: Optimized for both transactional and analytical workloads
5. **Security**: Role-based access control and data encryption

### Schema Overview

The database consists of several main domains:

- **User Management**: Users, roles, permissions, sessions
- **Academic Management**: Students, teachers, classes, subjects
- **Learning Management**: Assignments, exams, grades, attendance
- **Financial Management**: Fees, payments, invoices, scholarships
- **Communication**: Messages, notifications, campaigns
- **Content Management**: CMS pages, news articles, media files
- **CRM**: Leads, contacts, communication tracking
- **Operations**: Library, transport, hostel, events

## Core Tables

### User Management

#### users
Primary user table for all system users.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(20) NOT NULL DEFAULT 'student',
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    last_login TIMESTAMP,
    profile_picture VARCHAR(500),
    date_of_birth DATE,
    gender VARCHAR(10),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(20),
    emergency_contact_relationship VARCHAR(50),
    notes TEXT,
    language_preference VARCHAR(5) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**
- `idx_users_email` ON email
- `idx_users_username` ON username
- `idx_users_role` ON role
- `idx_users_active` ON is_active

#### user_sessions
Tracks active user sessions for security.

```sql
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_type VARCHAR(50),
    location VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Academic Management

#### students
Student-specific information extending user data.

```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
    student_id VARCHAR(50) UNIQUE NOT NULL,
    admission_date DATE NOT NULL,
    current_class_id INTEGER REFERENCES classes(id),
    academic_year VARCHAR(20) NOT NULL,
    roll_number VARCHAR(20),
    section VARCHAR(10),
    blood_group VARCHAR(5),
    allergies TEXT,
    medical_conditions TEXT,
    transportation_mode VARCHAR(50),
    bus_route_id INTEGER REFERENCES bus_routes(id),
    hostel_room_id INTEGER REFERENCES hostel_rooms(id),
    is_hosteller BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    graduation_date DATE,
    dropout_date DATE,
    dropout_reason TEXT,
    previous_school VARCHAR(200),
    transfer_certificate_number VARCHAR(100),
    hobbies TEXT,
    special_needs TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### teachers
Teacher-specific information extending user data.

```sql
CREATE TABLE teachers (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    qualification VARCHAR(200),
    specialization VARCHAR(200),
    experience_years INTEGER,
    joining_date DATE NOT NULL,
    department VARCHAR(100),
    designation VARCHAR(100),
    employment_type VARCHAR(50) NOT NULL,
    salary FLOAT,
    bank_account_number VARCHAR(50),
    bank_name VARCHAR(100),
    bank_ifsc VARCHAR(20),
    alternative_phone VARCHAR(20),
    last_appraisal_date DATE,
    next_appraisal_date DATE,
    performance_rating FLOAT,
    is_active BOOLEAN DEFAULT true,
    resignation_date DATE,
    resignation_reason TEXT,
    teaching_philosophy TEXT,
    awards_recognitions TEXT,
    publications TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### classes
Academic classes/grades in the school.

```sql
CREATE TABLE classes (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    section VARCHAR(10),
    grade_level INTEGER NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    capacity INTEGER,
    class_teacher_id INTEGER REFERENCES teachers(id),
    room_number VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### subjects
Academic subjects taught in the school.

```sql
CREATE TABLE subjects (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    department VARCHAR(100),
    category VARCHAR(50),
    credits INTEGER,
    theory_hours INTEGER,
    practical_hours INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Learning Management

#### assignments
Homework and project assignments.

```sql
CREATE TABLE assignments (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    class_id INTEGER NOT NULL REFERENCES classes(id),
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    teacher_id INTEGER NOT NULL REFERENCES teachers(id),
    assignment_type VARCHAR(50) NOT NULL,
    instructions TEXT,
    max_score FLOAT DEFAULT 100.0,
    assigned_date TIMESTAMP NOT NULL,
    due_date TIMESTAMP NOT NULL,
    late_submission_allowed BOOLEAN DEFAULT true,
    late_penalty_percentage FLOAT,
    attachment_paths JSON,
    is_published BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### assignment_submissions
Student submissions for assignments.

```sql
CREATE TABLE assignment_submissions (
    id INTEGER PRIMARY KEY,
    assignment_id INTEGER NOT NULL REFERENCES assignments(id),
    student_id INTEGER NOT NULL REFERENCES students(id),
    submission_text TEXT,
    attachment_paths JSON,
    submitted_at TIMESTAMP NOT NULL,
    is_late BOOLEAN DEFAULT false,
    attempt_number INTEGER DEFAULT 1,
    score FLOAT,
    grade_letter VARCHAR(5),
    feedback TEXT,
    graded_by INTEGER REFERENCES users(id),
    graded_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'submitted',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### grades
Student academic grades.

```sql
CREATE TABLE grades (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    assessment_type VARCHAR(50) NOT NULL,
    assessment_id INTEGER,
    assessment_name VARCHAR(200) NOT NULL,
    score FLOAT NOT NULL,
    max_score FLOAT NOT NULL,
    grade_letter VARCHAR(5),
    grade_points FLOAT,
    percentage FLOAT,
    term VARCHAR(20) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    comments TEXT,
    graded_by INTEGER NOT NULL REFERENCES users(id),
    graded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### attendance_records
Daily attendance tracking for students.

```sql
CREATE TABLE attendance_records (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    class_id INTEGER NOT NULL REFERENCES classes(id),
    date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    check_in_time TIMESTAMP,
    check_out_time TIMESTAMP,
    reason TEXT,
    marked_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Financial Management

#### fee_types
Types of fees (tuition, transport, etc.).

```sql
CREATE TABLE fee_types (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(50),
    is_mandatory BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### fee_structures
Fee amounts for different classes and years.

```sql
CREATE TABLE fee_structures (
    id INTEGER PRIMARY KEY,
    fee_type_id INTEGER NOT NULL REFERENCES fee_types(id),
    class_id INTEGER REFERENCES classes(id),
    academic_year VARCHAR(20) NOT NULL,
    amount FLOAT NOT NULL,
    due_date DATE NOT NULL,
    frequency VARCHAR(20) NOT NULL,
    installments INTEGER DEFAULT 1,
    late_fee_amount FLOAT DEFAULT 0.0,
    late_fee_percentage FLOAT DEFAULT 0.0,
    discount_percentage FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### fee_payments
Student fee payment records.

```sql
CREATE TABLE fee_payments (
    id INTEGER PRIMARY KEY,
    payment_reference VARCHAR(100) UNIQUE NOT NULL,
    student_id INTEGER NOT NULL REFERENCES students(id),
    invoice_id INTEGER REFERENCES invoices(id),
    fee_structure_id INTEGER NOT NULL REFERENCES fee_structures(id),
    amount FLOAT NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_date DATE NOT NULL,
    transaction_id VARCHAR(100),
    gateway_response JSON,
    bank_details JSON,
    status VARCHAR(20) DEFAULT 'pending',
    received_by INTEGER REFERENCES users(id),
    receipt_number VARCHAR(50),
    notes TEXT,
    refund_amount FLOAT DEFAULT 0.0,
    refund_reason TEXT,
    refunded_by INTEGER REFERENCES users(id),
    refund_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Communication

#### notifications
System notifications to users.

```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    action_url VARCHAR(500),
    action_text VARCHAR(100),
    data JSON,
    channels JSON,
    is_read BOOLEAN DEFAULT false,
    is_sent BOOLEAN DEFAULT false,
    priority VARCHAR(20) DEFAULT 'normal',
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    expires_at TIMESTAMP,
    source_type VARCHAR(50),
    source_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Relationships and Constraints

### Foreign Key Relationships

1. **Users → Students/Teachers/Parents**: One-to-one relationships extending user profiles
2. **Students → Classes**: Many-to-one (current class assignment)
3. **Teachers → Subjects**: Many-to-many (subjects taught)
4. **Classes → Subjects**: Many-to-many (subjects offered)
5. **Students → Assignments**: One-to-many (assignment submissions)
6. **Students → Grades**: One-to-many (academic performance)

### Key Constraints

- **Unique Constraints**: Email addresses, student IDs, employee IDs
- **Check Constraints**: Valid date ranges, positive amounts
- **Not Null Constraints**: Essential fields like names, IDs

## Performance Optimizations

### Indexing Strategy

```sql
-- User-related indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

-- Academic indexes
CREATE INDEX idx_students_class ON students(current_class_id);
CREATE INDEX idx_students_academic_year ON students(academic_year);
CREATE INDEX idx_grades_student_subject ON grades(student_id, subject_id);
CREATE INDEX idx_attendance_student_date ON attendance_records(student_id, date);

-- Financial indexes
CREATE INDEX idx_payments_student ON fee_payments(student_id);
CREATE INDEX idx_payments_date ON fee_payments(payment_date);
CREATE INDEX idx_payments_status ON fee_payments(status);

-- Communication indexes
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(is_read);
CREATE INDEX idx_notifications_created ON notifications(created_at);
```

### Query Optimization

1. **Partitioning**: Large tables partitioned by academic year
2. **Materialized Views**: Pre-computed aggregations for reports
3. **Connection Pooling**: Efficient database connection management
4. **Query Caching**: Frequently accessed data cached in Redis

## Data Migration and Backup

### Migration Strategy

1. **Schema Versioning**: All schema changes tracked with migrations
2. **Data Validation**: Constraints ensure data integrity during migrations
3. **Rollback Support**: All migrations include rollback procedures

### Backup Strategy

1. **Daily Backups**: Full database backup every night
2. **Incremental Backups**: Transaction log backups every hour
3. **Long-term Retention**: Monthly backups kept for 7 years
4. **Disaster Recovery**: Cross-region backup replication

## Security Considerations

### Data Protection

1. **Encryption at Rest**: Database files encrypted with AES-256
2. **Encryption in Transit**: All connections use TLS 1.3
3. **Access Control**: Role-based permissions at database level
4. **Audit Logging**: All data modifications logged

### Privacy Compliance

1. **FERPA Compliance**: Student data protection measures
2. **GDPR Compliance**: Data subject rights implementation
3. **Data Retention**: Automated cleanup of expired data
4. **Anonymization**: PII anonymization for analytics

## Monitoring and Maintenance

### Health Monitoring

1. **Performance Metrics**: Query performance tracking
2. **Storage Monitoring**: Disk space and growth tracking
3. **Connection Monitoring**: Active connection tracking
4. **Error Logging**: Database error logging and alerting

### Maintenance Tasks

1. **Statistics Updates**: Regular statistics refresh for query optimization
2. **Index Maintenance**: Index rebuilding and reorganization
3. **Data Cleanup**: Removal of expired sessions and temporary data
4. **Vacuum Operations**: Regular database maintenance for optimal performance

## Troubleshooting

### Common Issues

1. **Slow Queries**: Check execution plans and indexes
2. **Lock Timeouts**: Identify long-running transactions
3. **Storage Issues**: Monitor disk space and growth
4. **Connection Issues**: Check connection pool settings

### Diagnostic Queries

```sql
-- Check table sizes
SELECT table_name, 
       pg_size_pretty(pg_total_relation_size(table_name)) as size
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check active connections
SELECT pid, usename, application_name, state, query_start
FROM pg_stat_activity 
WHERE state = 'active';
```
