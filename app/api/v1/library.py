"""
Library and Inventory API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.models import library as models
from app.schemas import library as schemas

router = APIRouter()

# Helper function to get an object or raise 404
def get_object_or_404(db: Session, model, object_id: int):
    obj = db.query(model).filter(model.id == object_id).first()
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return obj

# BookCategory endpoints
@router.post("/book-categories/", response_model=schemas.BookCategory, status_code=201)
def create_book_category(category: schemas.BookCategoryCreate, db: Session = Depends(get_db)):
    db_category = models.BookCategory(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/book-categories/", response_model=List[schemas.BookCategory])
def read_book_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.BookCategory).offset(skip).limit(limit).all()

@router.get("/book-categories/{category_id}", response_model=schemas.BookCategory)
def read_book_category(category_id: int, db: Session = Depends(get_db)):
    return get_object_or_404(db, models.BookCategory, category_id)

@router.put("/book-categories/{category_id}", response_model=schemas.BookCategory)
def update_book_category(category_id: int, category: schemas.BookCategoryUpdate, db: Session = Depends(get_db)):
    db_category = get_object_or_404(db, models.BookCategory, category_id)
    for key, value in category.dict().items():
        setattr(db_category, key, value)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/book-categories/{category_id}", status_code=204)
def delete_book_category(category_id: int, db: Session = Depends(get_db)):
    db_category = get_object_or_404(db, models.BookCategory, category_id)
    db.delete(db_category)
    db.commit()
    return

# Book endpoints
@router.post("/books/", response_model=schemas.Book, status_code=201)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    db_book = models.Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@router.get("/books/", response_model=List[schemas.Book])
def read_books(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Book).offset(skip).limit(limit).all()

@router.get("/books/{book_id}", response_model=schemas.Book)
def read_book(book_id: int, db: Session = Depends(get_db)):
    return get_object_or_404(db, models.Book, book_id)

@router.put("/books/{book_id}", response_model=schemas.Book)
def update_book(book_id: int, book: schemas.BookUpdate, db: Session = Depends(get_db)):
    db_book = get_object_or_404(db, models.Book, book_id)
    for key, value in book.dict().items():
        setattr(db_book, key, value)
    db.commit()
    db.refresh(db_book)
    return db_book

@router.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    db_book = get_object_or_404(db, models.Book, book_id)
    db.delete(db_book)
    db.commit()
    return

# LibraryMember endpoints
@router.post("/library-members/", response_model=schemas.LibraryMember, status_code=201)
def create_library_member(member: schemas.LibraryMemberCreate, db: Session = Depends(get_db)):
    db_member = models.LibraryMember(**member.dict())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

@router.get("/library-members/", response_model=List[schemas.LibraryMember])
def read_library_members(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.LibraryMember).offset(skip).limit(limit).all()

# BookIssue endpoints
@router.post("/book-issues/", response_model=schemas.BookIssue, status_code=201)
def create_book_issue(issue: schemas.BookIssueCreate, db: Session = Depends(get_db)):
    db_issue = models.BookIssue(**issue.dict())
    # TODO: Decrement available_copies of the book
    db.add(db_issue)
    db.commit()
    db.refresh(db_issue)
    return db_issue

@router.get("/book-issues/", response_model=List[schemas.BookIssue])
def read_book_issues(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.BookIssue).offset(skip).limit(limit).all()

# InventoryCategory endpoints
@router.post("/inventory-categories/", response_model=schemas.InventoryCategory, status_code=201)
def create_inventory_category(category: schemas.InventoryCategoryCreate, db: Session = Depends(get_db)):
    db_category = models.InventoryCategory(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/inventory-categories/", response_model=List[schemas.InventoryCategory])
def read_inventory_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.InventoryCategory).offset(skip).limit(limit).all()

# InventoryItem endpoints
@router.post("/inventory-items/", response_model=schemas.InventoryItem, status_code=201)
def create_inventory_item(item: schemas.InventoryItemCreate, db: Session = Depends(get_db)):
    db_item = models.InventoryItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/inventory-items/", response_model=List[schemas.InventoryItem])
def read_inventory_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.InventoryItem).offset(skip).limit(limit).all()

# InventoryIssue endpoints
@router.post("/inventory-issues/", response_model=schemas.InventoryIssue, status_code=201)
def create_inventory_issue(issue: schemas.InventoryIssueCreate, db: Session = Depends(get_db)):
    db_issue = models.InventoryIssue(**issue.dict())
    # TODO: Decrement quantity of the inventory item
    db.add(db_issue)
    db.commit()
    db.refresh(db_issue)
    return db_issue

@router.get("/inventory-issues/", response_model=List[schemas.InventoryIssue])
def read_inventory_issues(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.InventoryIssue).offset(skip).limit(limit).all()
