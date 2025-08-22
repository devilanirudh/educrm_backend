"""Financial models for fees, invoices, and transactions."""

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database.session import Base

class FeeCategory(enum.Enum):
    TUITION = "tuition"
    TRANSPORT = "transport"
    LIBRARY = "library"
    EXAM = "exam"
    HOSTEL = "hostel"
    MISCELLANEOUS = "miscellaneous"

class PaymentMethod(enum.Enum):
    CASH = "cash"
    CARD = "card"
    UPI = "upi"
    NETBANKING = "netbanking"
    WALLET = "wallet"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"

class FeeType(Base):
    __tablename__ = "fee_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    is_mandatory = Column(Boolean, default=True)

class FeeStructure(Base):
    __tablename__ = "fee_structures"

    id = Column(Integer, primary_key=True, index=True)
    fee_type_id = Column(Integer, ForeignKey("fee_types.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    academic_year = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(Date, nullable=False)
    frequency = Column(String, nullable=False, default="monthly")

    fee_type = relationship("FeeType")
    class_obj = relationship("Class")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    fee_structure_id = Column(Integer, ForeignKey("fee_structures.id"), nullable=False)
    amount_due = Column(Float, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    student = relationship("Student")
    fee_structure = relationship("FeeStructure")
    transactions = relationship("Transaction", back_populates="invoice")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    amount_paid = Column(Float, nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False)
    receipt_number = Column(String, unique=True, index=True)
    
    invoice = relationship("Invoice", back_populates="transactions")
