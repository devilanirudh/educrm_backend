"""
Hostel and accommodation management database models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class HostelBlock(Base):
    """Hostel blocks or buildings"""
    __tablename__ = "hostel_blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    block_name = Column(String(100), nullable=False, unique=True)
    block_code = Column(String(20), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Block details
    total_floors = Column(Integer, nullable=False, default=1)
    total_rooms = Column(Integer, nullable=False, default=0)
    
    # Amenities
    has_wifi = Column(Boolean, default=True, nullable=False)
    has_laundry = Column(Boolean, default=False, nullable=False)
    has_common_room = Column(Boolean, default=False, nullable=False)
    has_study_hall = Column(Boolean, default=False, nullable=False)
    
    # Staff
    warden_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    warden = relationship("User")
    rooms = relationship("HostelRoom", back_populates="block", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<HostelBlock(id={self.id}, name='{self.block_name}', code='{self.block_code}')>"


class HostelRoom(Base):
    """Individual hostel rooms"""
    __tablename__ = "hostel_rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(Integer, ForeignKey("hostel_blocks.id"), nullable=False)
    room_number = Column(String(20), nullable=False)
    floor = Column(Integer, nullable=False, default=1)
    
    # Room details
    room_type = Column(String(50), nullable=False)  # single, double, triple, dormitory
    max_occupancy = Column(Integer, nullable=False, default=2)
    current_occupancy = Column(Integer, nullable=False, default=0)
    
    # Amenities
    has_attached_bathroom = Column(Boolean, default=False, nullable=False)
    has_ac = Column(Boolean, default=False, nullable=False)
    has_fan = Column(Boolean, default=True, nullable=False)
    has_study_table = Column(Boolean, default=True, nullable=False)
    has_wardrobe = Column(Boolean, default=True, nullable=False)
    
    # Pricing
    monthly_fee = Column(Float, nullable=True)
    security_deposit = Column(Float, nullable=True)
    
    # Status
    is_available = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Maintenance
    last_cleaned = Column(Date, nullable=True)
    last_maintenance = Column(Date, nullable=True)
    condition = Column(String(20), nullable=False, default="good")  # excellent, good, fair, poor
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    block = relationship("HostelBlock", back_populates="rooms")
    students = relationship("Student", foreign_keys="Student.hostel_room_id", back_populates="hostel_room")
    allocations = relationship("HostelAllocation", back_populates="room", cascade="all, delete-orphan")
    maintenance_requests = relationship("HostelMaintenanceRequest", back_populates="room", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<HostelRoom(id={self.id}, block_id={self.block_id}, number='{self.room_number}')>"


class HostelAllocation(Base):
    """Student hostel room allocations"""
    __tablename__ = "hostel_allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("hostel_rooms.id"), nullable=False)
    
    # Allocation details
    allocation_date = Column(Date, nullable=False)
    check_in_date = Column(Date, nullable=True)
    check_out_date = Column(Date, nullable=True)
    planned_check_out = Column(Date, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="allocated")  # allocated, checked_in, checked_out, cancelled
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Fees
    monthly_fee = Column(Float, nullable=True)
    security_deposit_paid = Column(Float, nullable=True)
    security_deposit_refunded = Column(Float, nullable=True)
    
    # Notes
    allocation_notes = Column(Text, nullable=True)
    check_in_notes = Column(Text, nullable=True)
    check_out_notes = Column(Text, nullable=True)
    
    # Allocated by
    allocated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    student = relationship("Student")
    room = relationship("HostelRoom", back_populates="allocations")
    allocator = relationship("User")
    
    def __repr__(self):
        return f"<HostelAllocation(id={self.id}, student_id={self.student_id}, room_id={self.room_id})>"


class HostelMaintenanceRequest(Base):
    """Hostel maintenance and repair requests"""
    __tablename__ = "hostel_maintenance_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("hostel_rooms.id"), nullable=False)
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Request details
    issue_type = Column(String(50), nullable=False)  # plumbing, electrical, furniture, cleaning, etc.
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="medium")  # low, medium, high, urgent
    
    # Status tracking
    status = Column(String(20), nullable=False, default="reported")  # reported, assigned, in_progress, completed, cancelled
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    estimated_completion = Column(DateTime(timezone=True), nullable=True)
    actual_completion = Column(DateTime(timezone=True), nullable=True)
    
    # Cost
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    
    # Resolution
    resolution_notes = Column(Text, nullable=True)
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5 scale
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    room = relationship("HostelRoom", back_populates="maintenance_requests")
    reporter = relationship("User", foreign_keys=[reported_by])
    assignee = relationship("User", foreign_keys=[assigned_to])
    
    def __repr__(self):
        return f"<HostelMaintenanceRequest(id={self.id}, room_id={self.room_id}, type='{self.issue_type}')>"


class HostelFeePayment(Base):
    """Hostel fee payments"""
    __tablename__ = "hostel_fee_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    allocation_id = Column(Integer, ForeignKey("hostel_allocations.id"), nullable=True)
    
    # Payment details
    payment_type = Column(String(50), nullable=False)  # monthly_fee, security_deposit, fine, etc.
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    payment_method = Column(String(50), nullable=False)  # cash, bank_transfer, online, cheque
    
    # Period covered
    fee_month = Column(String(20), nullable=True)  # "2024-01" for monthly fees
    fee_year = Column(Integer, nullable=True)
    
    # Transaction details
    transaction_id = Column(String(100), nullable=True)
    receipt_number = Column(String(100), nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="completed")  # pending, completed, failed, refunded
    
    # Collected by
    collected_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    student = relationship("Student")
    allocation = relationship("HostelAllocation")
    collector = relationship("User")
    
    def __repr__(self):
        return f"<HostelFeePayment(id={self.id}, student_id={self.student_id}, amount={self.amount})>"


class HostelAttendance(Base):
    """Daily hostel attendance tracking"""
    __tablename__ = "hostel_attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("hostel_rooms.id"), nullable=False)
    
    # Attendance details
    date = Column(Date, nullable=False, index=True)
    check_in_time = Column(DateTime(timezone=True), nullable=True)
    check_out_time = Column(DateTime(timezone=True), nullable=True)
    is_present_night = Column(Boolean, nullable=True)  # Stayed for the night
    
    # Status
    status = Column(String(20), nullable=False)  # present, absent, late, leave
    leave_reason = Column(Text, nullable=True)
    
    # Marked by
    marked_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    student = relationship("Student")
    room = relationship("HostelRoom")
    marker = relationship("User")
    
    def __repr__(self):
        return f"<HostelAttendance(student_id={self.student_id}, date={self.date}, status='{self.status}')>"
