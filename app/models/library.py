"""
Library and Inventory management database models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Date, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class BookCategory(Base):
    __tablename__ = "book_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    books = relationship("Book", back_populates="category")

class Book(Base):
    """Books in the library"""
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(20), unique=True, index=True, nullable=True)
    title = Column(String(300), nullable=False, index=True)
    author = Column(String(200), nullable=False)
    publisher = Column(String(200), nullable=True)
    publication_year = Column(Integer, nullable=True)
    
    category_id = Column(Integer, ForeignKey("book_categories.id"))
    category = relationship("BookCategory", back_populates="books")
    
    total_copies = Column(Integer, default=1, nullable=False)
    available_copies = Column(Integer, default=1, nullable=False)
    
    issues = relationship("BookIssue", back_populates="book")

class LibraryMember(Base):
    __tablename__ = "library_members"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    member_type = Column(String(50)) # Student, Teacher

    user = relationship("User")
    issues = relationship("BookIssue", back_populates="member")

class BookIssue(Base):
    __tablename__ = "book_issues"
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("library_members.id"), nullable=False)
    
    issue_date = Column(Date, default=func.current_date(), nullable=False)
    due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    
    book = relationship("Book", back_populates="issues")
    member = relationship("LibraryMember", back_populates="issues")

class InventoryCategory(Base):
    __tablename__ = "inventory_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    items = relationship("InventoryItem", back_populates="category")

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    sku = Column(String(50), unique=True, index=True, nullable=True)
    
    category_id = Column(Integer, ForeignKey("inventory_categories.id"))
    category = relationship("InventoryCategory", back_populates="items")
    
    quantity = Column(Integer, default=1, nullable=False)
    location = Column(String(100), nullable=True)
    
    issues = relationship("InventoryIssue", back_populates="item")

class InventoryIssue(Base):
    __tablename__ = "inventory_issues"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Staff member
    
    issue_date = Column(Date, default=func.current_date(), nullable=False)
    return_date = Column(Date, nullable=True)
    
    item = relationship("InventoryItem", back_populates="issues")
    user = relationship("User")
