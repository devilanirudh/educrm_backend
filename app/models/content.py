"""
Content Management System (CMS) database models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class CMSPage(Base):
    """CMS pages for website content"""
    __tablename__ = "cms_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    excerpt = Column(Text, nullable=True)
    
    # Page metadata
    page_type = Column(String(50), nullable=False, default="page")  # page, post, event
    template = Column(String(100), nullable=True)
    parent_id = Column(Integer, ForeignKey("cms_pages.id"), nullable=True)
    
    # SEO
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(Text, nullable=True)
    meta_keywords = Column(Text, nullable=True)
    
    # Media
    featured_image = Column(String(500), nullable=True)
    gallery_images = Column(JSON, nullable=True)  # List of image paths
    
    # Status and permissions
    status = Column(String(20), nullable=False, default="draft")  # draft, published, archived
    is_published = Column(Boolean, default=False, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    visibility = Column(String(20), nullable=False, default="public")  # public, private, protected
    
    # Publishing
    published_at = Column(DateTime(timezone=True), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    editor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Ordering and display
    sort_order = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    author = relationship("User", foreign_keys=[author_id])
    editor = relationship("User", foreign_keys=[editor_id])
    parent = relationship("CMSPage", remote_side=[id])
    children = relationship("CMSPage", cascade="all, delete-orphan", overlaps="parent")
    comments = relationship("CMSComment", back_populates="page", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CMSPage(id={self.id}, title='{self.title}', slug='{self.slug}')>"


class NewsArticle(Base):
    """News articles and announcements"""
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    excerpt = Column(Text, nullable=True)
    
    # Article metadata
    category = Column(String(100), nullable=True)  # academic, sports, events, general
    tags = Column(JSON, nullable=True)  # List of tags
    
    # SEO
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(Text, nullable=True)
    
    # Media
    featured_image = Column(String(500), nullable=True)
    gallery_images = Column(JSON, nullable=True)  # List of image paths
    
    # Status and permissions
    status = Column(String(20), nullable=False, default="draft")  # draft, published, archived
    is_published = Column(Boolean, default=False, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    is_breaking = Column(Boolean, default=False, nullable=False)
    
    # Publishing
    published_at = Column(DateTime(timezone=True), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    editor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Engagement
    view_count = Column(Integer, default=0, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)
    share_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    author = relationship("User", foreign_keys=[author_id])
    editor = relationship("User", foreign_keys=[editor_id])
    comments = relationship("NewsComment", back_populates="article", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title='{self.title}', slug='{self.slug}')>"


class MediaFile(Base):
    """Media files (images, videos, documents)"""
    __tablename__ = "media_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=True)
    
    # File metadata
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(100), nullable=False)  # image, video, document, audio
    mime_type = Column(String(100), nullable=False)
    file_extension = Column(String(10), nullable=False)
    
    # Image metadata (if applicable)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)  # For video/audio files
    
    # Organization
    category = Column(String(100), nullable=True)  # gallery, documents, avatars, etc.
    alt_text = Column(String(255), nullable=True)
    caption = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    # Upload details
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_ip = Column(String(45), nullable=True)
    
    # Status
    is_public = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    uploader = relationship("User")
    
    def __repr__(self):
        return f"<MediaFile(id={self.id}, filename='{self.filename}', type='{self.file_type}')>"


class CMSComment(Base):
    """Comments on CMS pages"""
    __tablename__ = "cms_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("cms_pages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for anonymous comments
    parent_id = Column(Integer, ForeignKey("cms_comments.id"), nullable=True)  # For nested comments
    
    # Comment content
    content = Column(Text, nullable=False)
    author_name = Column(String(100), nullable=True)  # For anonymous comments
    author_email = Column(String(255), nullable=True)  # For anonymous comments
    
    # Status
    status = Column(String(20), nullable=False, default="pending")  # pending, approved, rejected, spam
    is_approved = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    page = relationship("CMSPage", back_populates="comments")
    user = relationship("User")
    parent = relationship("CMSComment", remote_side=[id])
    children = relationship("CMSComment", cascade="all, delete-orphan", overlaps="parent")
    
    def __repr__(self):
        return f"<CMSComment(id={self.id}, page_id={self.page_id}, status='{self.status}')>"


class NewsComment(Base):
    """Comments on news articles"""
    __tablename__ = "news_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_articles.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for anonymous comments
    parent_id = Column(Integer, ForeignKey("news_comments.id"), nullable=True)  # For nested comments
    
    # Comment content
    content = Column(Text, nullable=False)
    author_name = Column(String(100), nullable=True)  # For anonymous comments
    author_email = Column(String(255), nullable=True)  # For anonymous comments
    
    # Status
    status = Column(String(20), nullable=False, default="pending")  # pending, approved, rejected, spam
    is_approved = Column(Boolean, default=False, nullable=False)
    
    # Engagement
    like_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    article = relationship("NewsArticle", back_populates="comments")
    user = relationship("User")
    parent = relationship("NewsComment", remote_side=[id])
    children = relationship("NewsComment", cascade="all, delete-orphan", overlaps="parent")
    
    def __repr__(self):
        return f"<NewsComment(id={self.id}, article_id={self.article_id}, status='{self.status}')>"


class MenuSection(Base):
    """Website navigation menu sections"""
    __tablename__ = "menu_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Menu configuration
    menu_type = Column(String(50), nullable=False, default="main")  # main, footer, sidebar
    parent_id = Column(Integer, ForeignKey("menu_sections.id"), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Display settings
    is_visible = Column(Boolean, default=True, nullable=False)
    icon = Column(String(100), nullable=True)
    css_class = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    parent = relationship("MenuSection", remote_side=[id])
    children = relationship("MenuSection", cascade="all, delete-orphan", overlaps="parent")
    menu_items = relationship("MenuItem", back_populates="section", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MenuSection(id={self.id}, name='{self.name}', type='{self.menu_type}')>"


class MenuItem(Base):
    """Website navigation menu items"""
    __tablename__ = "menu_items"
    
    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("menu_sections.id"), nullable=False)
    title = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    
    # Menu item configuration
    target = Column(String(20), nullable=False, default="_self")  # _self, _blank, _parent, _top
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Display settings
    is_visible = Column(Boolean, default=True, nullable=False)
    icon = Column(String(100), nullable=True)
    css_class = Column(String(100), nullable=True)
    
    # Access control
    required_role = Column(String(50), nullable=True)  # Role required to see this menu item
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    section = relationship("MenuSection", back_populates="menu_items")
    
    def __repr__(self):
        return f"<MenuItem(id={self.id}, title='{self.title}', url='{self.url}')>"


class WebsiteSettings(Base):
    """Website configuration and settings"""
    __tablename__ = "website_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, index=True, nullable=False)
    setting_value = Column(Text, nullable=True)
    setting_type = Column(String(50), nullable=False, default="text")  # text, number, boolean, json, image
    category = Column(String(100), nullable=False, default="general")  # general, appearance, seo, social
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)  # Can be accessed via public API
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<WebsiteSettings(key='{self.setting_key}', category='{self.category}')>"
