"""fees API endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.financial import FeeStructure, Invoice, Transaction
from app.schemas.financial import FeeStructureCreate, FeeStructureResponse, FeeStructureUpdate, InvoiceCreate, InvoiceResponse, TransactionCreate, TransactionResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/structures", response_model=FeeStructureResponse)
async def create_fee_structure(
    fee_structure: FeeStructureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new fee structure"""
    db_fee_structure = FeeStructure(**fee_structure.dict())
    db.add(db_fee_structure)
    db.commit()
    db.refresh(db_fee_structure)
    return db_fee_structure

@router.get("/structures", response_model=List[FeeStructureResponse])
async def get_fee_structures(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all fee structures"""
    fee_structures = db.query(FeeStructure).all()
    return fee_structures

@router.put("/structures/{structure_id}", response_model=FeeStructureResponse)
async def update_fee_structure(
    structure_id: int,
    fee_structure: FeeStructureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a fee structure"""
    db_fee_structure = db.query(FeeStructure).filter(FeeStructure.id == structure_id).first()
    if not db_fee_structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")
    
    for field, value in fee_structure.dict(exclude_unset=True).items():
        setattr(db_fee_structure, field, value)
        
    db.commit()
    db.refresh(db_fee_structure)
    return db_fee_structure

@router.delete("/structures/{structure_id}", status_code=204)
async def delete_fee_structure(
    structure_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a fee structure"""
    db_fee_structure = db.query(FeeStructure).filter(FeeStructure.id == structure_id).first()
    if not db_fee_structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")
    
    db.delete(db_fee_structure)
    db.commit()
    return {"ok": True}

@router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(
    invoice: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new invoice"""
    db_invoice = Invoice(**invoice.dict())
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all invoices"""
    invoices = db.query(Invoice).all()
    return invoices

@router.post("/payments", response_model=TransactionResponse)
async def create_payment(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new payment"""
    db_transaction = Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all transactions"""
    transactions = db.query(Transaction).all()
    return transactions

@router.get("/transactions/recent", response_model=List[TransactionResponse])
async def get_recent_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the 10 most recent transactions"""
    transactions = db.query(Transaction).order_by(Transaction.payment_date.desc()).limit(10).all()
    return transactions
