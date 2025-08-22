"""
Pydantic schemas for Library and Inventory
"""

from pydantic import BaseModel
from typing import Optional
from datetime import date

# BookCategory Schemas
class BookCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class BookCategoryCreate(BookCategoryBase):
    pass

class BookCategoryUpdate(BookCategoryBase):
    pass

class BookCategory(BookCategoryBase):
    id: int

    class Config:
        orm_mode = True

# Book Schemas
class BookBase(BaseModel):
    isbn: Optional[str] = None
    title: str
    author: str
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    category_id: int
    total_copies: int = 1
    available_copies: int = 1

class BookCreate(BookBase):
    pass

class BookUpdate(BookBase):
    pass

class Book(BookBase):
    id: int

    class Config:
        orm_mode = True

# LibraryMember Schemas
class LibraryMemberBase(BaseModel):
    user_id: int
    member_type: str

class LibraryMemberCreate(LibraryMemberBase):
    pass

class LibraryMemberUpdate(LibraryMemberBase):
    pass

class LibraryMember(LibraryMemberBase):
    id: int

    class Config:
        orm_mode = True

# BookIssue Schemas
class BookIssueBase(BaseModel):
    book_id: int
    member_id: int
    due_date: date
    return_date: Optional[date] = None

class BookIssueCreate(BookIssueBase):
    pass

class BookIssueUpdate(BookIssueBase):
    pass

class BookIssue(BookIssueBase):
    id: int
    issue_date: date

    class Config:
        orm_mode = True

# InventoryCategory Schemas
class InventoryCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class InventoryCategoryCreate(InventoryCategoryBase):
    pass

class InventoryCategoryUpdate(InventoryCategoryBase):
    pass

class InventoryCategory(InventoryCategoryBase):
    id: int

    class Config:
        orm_mode = True

# InventoryItem Schemas
class InventoryItemBase(BaseModel):
    name: str
    sku: Optional[str] = None
    category_id: int
    quantity: int = 1
    location: Optional[str] = None

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemUpdate(InventoryItemBase):
    pass

class InventoryItem(InventoryItemBase):
    id: int

    class Config:
        orm_mode = True

# InventoryIssue Schemas
class InventoryIssueBase(BaseModel):
    item_id: int
    user_id: int
    return_date: Optional[date] = None

class InventoryIssueCreate(InventoryIssueBase):
    pass

class InventoryIssueUpdate(InventoryIssueBase):
    pass

class InventoryIssue(InventoryIssueBase):
    id: int
    issue_date: date

    class Config:
        orm_mode = True