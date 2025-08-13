"""
Library management database models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Date, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class Book(Base):
    """Books in the library"""
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(20), unique=True, index=True, nullable=True)
    title = Column(String(300), nullable=False, index=True)
    author = Column(String(200), nullable=False)
    publisher = Column(String(200), nullable=True)
    publication_year = Column(Integer, nullable=True)
    edition = Column(String(50), nullable=True)
    
    # Classification
    category = Column(String(100), nullable=True)
    subject = Column(String(100), nullable=True)
    grade_level = Column(String(50), nullable=True)
    language = Column(String(50), default="English", nullable=False)
    
    # Physical properties
    pages = Column(Integer, nullable=True)
    format = Column(String(50), nullable=True)  # hardcover, paperback, ebook
    
    # Inventory
    total_copies = Column(Integer, default=1, nullable=False)
    available_copies = Column(Integer, default=1, nullable=False)
    price = Column(Float, nullable=True)
    location = Column(String(100), nullable=True)  # Shelf location
    
    # Description
    description = Column(Text, nullable=True)
    cover_image = Column(String(500), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_reference_only = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    transactions = relationship("LibraryTransaction", back_populates="book", cascade="all, delete-orphan")
    reservations = relationship("BookReservation", back_populates="book", cascade="all, delete-orphan")
    reviews = relationship("BookReview", back_populates="book", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', author='{self.author}')>"
    
    @property
    def is_available(self):
        return self.available_copies > 0 and self.is_active


class LibraryTransaction(Base):
    """Book borrowing and returning transactions"""
    __tablename__ = "library_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    
    # Transaction details
    transaction_type = Column(String(20), nullable=False)  # borrow, return, renew
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    
    # Staff details
    issued_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    returned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="active")  # active, returned, overdue, lost
    
    # Fine details
    fine_amount = Column(Float, default=0.0, nullable=False)
    fine_paid = Column(Boolean, default=False, nullable=False)
    fine_paid_date = Column(Date, nullable=True)
    
    # Notes
    issue_notes = Column(Text, nullable=True)
    return_notes = Column(Text, nullable=True)
    condition_at_issue = Column(String(50), nullable=True)  # good, fair, poor
    condition_at_return = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    book = relationship("Book", back_populates="transactions")
    student = relationship("Student", back_populates="library_transactions")
    issuer = relationship("User", foreign_keys=[issued_by])
    receiver = relationship("User", foreign_keys=[returned_to])
    
    def __repr__(self):
        return f"<LibraryTransaction(id={self.id}, book_id={self.book_id}, student_id={self.student_id}, status='{self.status}')>"
    
    @property
    def is_overdue(self):
        from datetime import date
        return self.status == "active" and self.due_date < date.today()
    
    @property
    def days_overdue(self):
        if self.is_overdue:
            from datetime import date
            return (date.today() - self.due_date).days
        return 0


class BookReservation(Base):
    """Book reservations"""
    __tablename__ = "book_reservations"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    
    # Reservation details
    reservation_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="active")  # active, fulfilled, cancelled, expired
    
    # Fulfillment
    fulfilled_date = Column(Date, nullable=True)
    fulfilled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    book = relationship("Book", back_populates="reservations")
    student = relationship("Student")
    fulfiller = relationship("User")
    
    def __repr__(self):
        return f"<BookReservation(id={self.id}, book_id={self.book_id}, student_id={self.student_id}, status='{self.status}')>"


class BookReview(Base):
    """Student book reviews and ratings"""
    __tablename__ = "book_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    
    # Review content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(200), nullable=True)
    review_text = Column(Text, nullable=True)
    
    # Status
    is_approved = Column(Boolean, default=False, nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    book = relationship("Book", back_populates="reviews")
    student = relationship("Student")
    approver = relationship("User")
    
    def __repr__(self):
        return f"<BookReview(id={self.id}, book_id={self.book_id}, rating={self.rating})>"


class LibrarySettings(Base):
    """Library configuration settings"""
    __tablename__ = "library_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Borrowing rules
    max_books_per_student = Column(Integer, default=3, nullable=False)
    default_loan_period_days = Column(Integer, default=14, nullable=False)
    max_renewals = Column(Integer, default=2, nullable=False)
    renewal_period_days = Column(Integer, default=7, nullable=False)
    
    # Fine settings
    fine_per_day = Column(Float, default=0.50, nullable=False)
    max_fine_amount = Column(Float, default=10.00, nullable=False)
    grace_period_days = Column(Integer, default=1, nullable=False)
    
    # Reservation settings
    reservation_expiry_days = Column(Integer, default=3, nullable=False)
    max_reservations_per_student = Column(Integer, default=2, nullable=False)
    
    # Library hours
    opening_time = Column(String(10), default="08:00", nullable=False)
    closing_time = Column(String(10), default="17:00", nullable=False)
    
    # Contact information
    librarian_name = Column(String(100), nullable=True)
    librarian_email = Column(String(255), nullable=True)
    librarian_phone = Column(String(20), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<LibrarySettings(id={self.id}, max_books={self.max_books_per_student})>"


class DigitalResource(Base):
    """Digital library resources (ebooks, videos, etc.)"""
    __tablename__ = "digital_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False, index=True)
    author = Column(String(200), nullable=True)
    publisher = Column(String(200), nullable=True)
    
    # Resource details
    resource_type = Column(String(50), nullable=False)  # ebook, video, audio, document
    file_format = Column(String(20), nullable=True)  # pdf, epub, mp4, mp3, etc.
    file_size = Column(Integer, nullable=True)  # in bytes
    file_path = Column(String(500), nullable=True)
    external_url = Column(String(500), nullable=True)
    
    # Classification
    category = Column(String(100), nullable=True)
    subject = Column(String(100), nullable=True)
    grade_level = Column(String(50), nullable=True)
    language = Column(String(50), default="English", nullable=False)
    
    # Access control
    access_type = Column(String(20), nullable=False, default="free")  # free, paid, subscription
    allowed_roles = Column(String(200), nullable=True)  # JSON list of allowed roles
    
    # Metadata
    description = Column(Text, nullable=True)
    thumbnail = Column(String(500), nullable=True)
    duration_minutes = Column(Integer, nullable=True)  # For videos/audio
    
    # Usage tracking
    download_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    access_logs = relationship("DigitalResourceAccess", back_populates="resource", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DigitalResource(id={self.id}, title='{self.title}', type='{self.resource_type}')>"


class DigitalResourceAccess(Base):
    """Digital resource access logs"""
    __tablename__ = "digital_resource_access"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("digital_resources.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Access details
    access_type = Column(String(20), nullable=False)  # view, download, stream
    access_date = Column(DateTime(timezone=True), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Usage tracking
    duration_seconds = Column(Integer, nullable=True)  # How long they accessed it
    completion_percentage = Column(Float, nullable=True)  # For videos/courses
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    resource = relationship("DigitalResource", back_populates="access_logs")
    user = relationship("User")
    
    def __repr__(self):
        return f"<DigitalResourceAccess(id={self.id}, resource_id={self.resource_id}, user_id={self.user_id})>"
