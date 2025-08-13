"""
Financial management database models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, Date, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class FeeType(Base):
    """Types of fees (tuition, transport, library, etc.)"""
    __tablename__ = "fee_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # academic, transport, hostel, etc.
    is_mandatory = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    fee_structures = relationship("FeeStructure", back_populates="fee_type", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FeeType(id={self.id}, name='{self.name}')>"


class FeeStructure(Base):
    """Fee structure for different classes and academic years"""
    __tablename__ = "fee_structures"
    
    id = Column(Integer, primary_key=True, index=True)
    fee_type_id = Column(Integer, ForeignKey("fee_types.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)  # Null for school-wide fees
    academic_year = Column(String(20), nullable=False)
    amount = Column(Float, nullable=False)
    
    # Payment schedule
    due_date = Column(Date, nullable=False)
    frequency = Column(String(20), nullable=False)  # monthly, quarterly, annually, one_time
    installments = Column(Integer, default=1, nullable=False)
    
    # Penalties and discounts
    late_fee_amount = Column(Float, default=0.0, nullable=False)
    late_fee_percentage = Column(Float, default=0.0, nullable=False)
    discount_percentage = Column(Float, default=0.0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    fee_type = relationship("FeeType", back_populates="fee_structures")
    class_info = relationship("Class")
    payments = relationship("FeePayment", back_populates="fee_structure", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="fee_structure", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FeeStructure(id={self.id}, fee_type_id={self.fee_type_id}, amount={self.amount})>"


class Invoice(Base):
    """Student fee invoices"""
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, index=True, nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    fee_structure_id = Column(Integer, ForeignKey("fee_structures.id"), nullable=False)
    
    # Invoice details
    amount = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0, nullable=False)
    late_fee_amount = Column(Float, default=0.0, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    # Dates
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    payment_deadline = Column(Date, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="pending")  # pending, paid, overdue, cancelled
    payment_status = Column(String(20), nullable=False, default="unpaid")  # unpaid, partial, paid, refunded
    
    # Additional information
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    student = relationship("Student")
    fee_structure = relationship("FeeStructure", back_populates="invoices")
    payments = relationship("FeePayment", back_populates="invoice", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', amount={self.total_amount})>"
    
    @property
    def amount_paid(self):
        return sum(payment.amount for payment in self.payments if payment.status == "completed")
    
    @property
    def amount_due(self):
        return max(0, self.total_amount - self.amount_paid)
    
    @property
    def is_overdue(self):
        from datetime import date
        return self.due_date < date.today() and self.payment_status != "paid"


class FeePayment(Base):
    """Fee payment records"""
    __tablename__ = "fee_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_reference = Column(String(100), unique=True, index=True, nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    fee_structure_id = Column(Integer, ForeignKey("fee_structures.id"), nullable=False)
    
    # Payment details
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)  # cash, card, bank_transfer, online, cheque
    payment_date = Column(Date, nullable=False)
    
    # Transaction details
    transaction_id = Column(String(100), nullable=True)
    gateway_response = Column(JSON, nullable=True)  # Payment gateway response
    bank_details = Column(JSON, nullable=True)  # Bank/card details
    
    # Status
    status = Column(String(20), nullable=False, default="pending")  # pending, completed, failed, cancelled, refunded
    
    # Additional information
    received_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    receipt_number = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Refund information
    refund_amount = Column(Float, default=0.0, nullable=False)
    refund_reason = Column(Text, nullable=True)
    refunded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    refund_date = Column(Date, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    student = relationship("Student", back_populates="fee_payments")
    invoice = relationship("Invoice", back_populates="payments")
    fee_structure = relationship("FeeStructure", back_populates="payments")
    receiver = relationship("User", foreign_keys=[received_by])
    refunder = relationship("User", foreign_keys=[refunded_by])
    
    def __repr__(self):
        return f"<FeePayment(id={self.id}, reference='{self.payment_reference}', amount={self.amount})>"


class Scholarship(Base):
    """Student scholarships and financial aid"""
    __tablename__ = "scholarships"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    scholarship_type = Column(String(50), nullable=False)  # merit, need_based, sports, arts, etc.
    
    # Eligibility criteria
    minimum_grade = Column(Float, nullable=True)
    maximum_family_income = Column(Float, nullable=True)
    eligible_classes = Column(JSON, nullable=True)  # List of class IDs
    
    # Scholarship details
    amount_type = Column(String(20), nullable=False)  # percentage, fixed_amount
    amount_value = Column(Float, nullable=False)
    max_amount = Column(Float, nullable=True)
    
    # Validity
    academic_year = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    application_deadline = Column(Date, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    max_recipients = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    applications = relationship("ScholarshipApplication", back_populates="scholarship", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Scholarship(id={self.id}, name='{self.name}')>"


class ScholarshipApplication(Base):
    """Student scholarship applications"""
    __tablename__ = "scholarship_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    scholarship_id = Column(Integer, ForeignKey("scholarships.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    
    # Application details
    application_date = Column(Date, nullable=False)
    family_income = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    supporting_documents = Column(JSON, nullable=True)  # List of document paths
    
    # Evaluation
    status = Column(String(20), nullable=False, default="pending")  # pending, approved, rejected, waitlisted
    evaluated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    evaluation_date = Column(Date, nullable=True)
    evaluation_comments = Column(Text, nullable=True)
    
    # Award details
    awarded_amount = Column(Float, nullable=True)
    award_percentage = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    scholarship = relationship("Scholarship", back_populates="applications")
    student = relationship("Student")
    evaluator = relationship("User")
    
    def __repr__(self):
        return f"<ScholarshipApplication(id={self.id}, scholarship_id={self.scholarship_id}, student_id={self.student_id})>"


class Expense(Base):
    """School expenses and expenditures"""
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    expense_number = Column(String(50), unique=True, index=True, nullable=False)
    category = Column(String(100), nullable=False)  # utilities, maintenance, salaries, supplies, etc.
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    
    # Expense details
    expense_date = Column(Date, nullable=False)
    vendor_name = Column(String(200), nullable=True)
    invoice_number = Column(String(100), nullable=True)
    payment_method = Column(String(50), nullable=False)
    
    # Approval workflow
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, approved, rejected, paid
    
    # Additional information
    receipt_path = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f"<Expense(id={self.id}, number='{self.expense_number}', amount={self.amount})>"


class FinancialReport(Base):
    """Financial reports and summaries"""
    __tablename__ = "financial_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_name = Column(String(200), nullable=False)
    report_type = Column(String(50), nullable=False)  # income, expense, balance_sheet, profit_loss
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Report data
    total_income = Column(Float, nullable=True)
    total_expenses = Column(Float, nullable=True)
    net_balance = Column(Float, nullable=True)
    report_data = Column(JSON, nullable=True)  # Detailed report data
    
    # Generation details
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    generation_date = Column(DateTime(timezone=True), nullable=False)
    report_path = Column(String(500), nullable=True)  # Path to generated report file
    
    # Status
    status = Column(String(20), nullable=False, default="generated")  # generated, approved, archived
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    generator = relationship("User")
    
    def __repr__(self):
        return f"<FinancialReport(id={self.id}, name='{self.report_name}', type='{self.report_type}')>"
