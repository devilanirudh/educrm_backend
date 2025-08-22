"""Pydantic schemas for financial data."""

from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

from app.models.financial import FeeCategory, PaymentMethod, PaymentStatus

class FeeStructureBase(BaseModel):
    fee_type_id: int
    amount: float
    due_date: date
    academic_year: str
    class_id: int

class FeeStructureCreate(FeeStructureBase):
    pass

class FeeStructureUpdate(BaseModel):
    fee_type_id: Optional[int] = None
    amount: Optional[float] = None
    due_date: Optional[date] = None
    academic_year: Optional[str] = None
    class_id: Optional[int] = None

class FeeStructureResponse(FeeStructureBase):
    id: int

    class Config:
        orm_mode = True

class InvoiceBase(BaseModel):
    student_id: int
    fee_structure_id: int
    amount_due: float
    due_date: date
    status: PaymentStatus

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceUpdate(InvoiceBase):
    pass

class InvoiceResponse(InvoiceBase):
    id: int

    class Config:
        orm_mode = True

class TransactionBase(BaseModel):
    invoice_id: int
    amount_paid: float
    payment_method: PaymentMethod
    status: PaymentStatus
    receipt_number: str

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    payment_date: datetime

    class Config:
        orm_mode = True