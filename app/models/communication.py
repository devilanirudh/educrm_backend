"""
Communication and notification database models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class Message(Base):
    """Internal messaging system"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(50), nullable=False, default="private")  # private, group, broadcast
    
    # Threading
    thread_id = Column(String(100), nullable=True)
    parent_message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    
    # Status
    is_draft = Column(Boolean, default=False, nullable=False)
    priority = Column(String(20), nullable=False, default="normal")  # low, normal, high, urgent
    
    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Attachments
    attachments = Column(JSON, nullable=True)  # List of file paths
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    parent_message = relationship("Message", remote_side=[id])
    replies = relationship("Message", cascade="all, delete-orphan", overlaps="parent_message")
    recipients = relationship("MessageRecipient", back_populates="message", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Message(id={self.id}, sender_id={self.sender_id}, subject='{self.subject}')>"


class MessageRecipient(Base):
    """Message recipients and read status"""
    __tablename__ = "message_recipients"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_type = Column(String(20), nullable=False, default="to")  # to, cc, bcc
    
    # Status
    is_read = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    is_starred = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    message = relationship("Message", back_populates="recipients")
    recipient = relationship("User")
    
    def __repr__(self):
        return f"<MessageRecipient(message_id={self.message_id}, recipient_id={self.recipient_id})>"


class Notification(Base):
    """User notifications"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # info, warning, error, success, reminder
    
    # Content and actions
    action_url = Column(String(500), nullable=True)
    action_text = Column(String(100), nullable=True)
    data = Column(JSON, nullable=True)  # Additional notification data
    
    # Channels
    channels = Column(JSON, nullable=True)  # List of delivery channels: web, email, sms, push
    
    # Status
    is_read = Column(Boolean, default=False, nullable=False)
    is_sent = Column(Boolean, default=False, nullable=False)
    priority = Column(String(20), nullable=False, default="normal")  # low, normal, high, urgent
    
    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Source
    source_type = Column(String(50), nullable=True)  # assignment, exam, fee, attendance, etc.
    source_id = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    delivery_logs = relationship("NotificationDeliveryLog", back_populates="notification", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.notification_type}')>"


class NotificationDeliveryLog(Base):
    """Notification delivery tracking"""
    __tablename__ = "notification_delivery_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False)
    channel = Column(String(20), nullable=False)  # web, email, sms, push
    
    # Delivery details
    recipient_address = Column(String(255), nullable=True)  # email, phone number
    status = Column(String(20), nullable=False, default="pending")  # pending, sent, delivered, failed, bounced
    attempt_count = Column(Integer, default=0, nullable=False)
    
    # Response details
    external_id = Column(String(255), nullable=True)  # Provider's message ID
    response_data = Column(JSON, nullable=True)  # Provider response
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    notification = relationship("Notification", back_populates="delivery_logs")
    
    def __repr__(self):
        return f"<NotificationDeliveryLog(id={self.id}, channel='{self.channel}', status='{self.status}')>"


class EmailTemplate(Base):
    """Email templates for automated communications"""
    __tablename__ = "email_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    subject = Column(String(200), nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=True)
    
    # Template metadata
    template_type = Column(String(50), nullable=False)  # admission, fee_reminder, grade_report, etc.
    description = Column(Text, nullable=True)
    variables = Column(JSON, nullable=True)  # List of available template variables
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<EmailTemplate(id={self.id}, name='{self.name}', type='{self.template_type}')>"


class SMSTemplate(Base):
    """SMS templates for automated communications"""
    __tablename__ = "sms_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    message = Column(Text, nullable=False)
    
    # Template metadata
    template_type = Column(String(50), nullable=False)  # admission, fee_reminder, attendance, etc.
    description = Column(Text, nullable=True)
    variables = Column(JSON, nullable=True)  # List of available template variables
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<SMSTemplate(id={self.id}, name='{self.name}', type='{self.template_type}')>"


class CommunicationCampaign(Base):
    """Communication campaigns for bulk messaging"""
    __tablename__ = "communication_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    campaign_type = Column(String(50), nullable=False)  # admission, fee_reminder, newsletter, announcement
    
    # Content
    subject = Column(String(200), nullable=True)  # For email campaigns
    message = Column(Text, nullable=False)
    
    # Targeting
    target_roles = Column(JSON, nullable=True)  # List of user roles
    target_classes = Column(JSON, nullable=True)  # List of class IDs
    target_users = Column(JSON, nullable=True)  # Specific user IDs
    
    # Channels
    channels = Column(JSON, nullable=False)  # email, sms, push, in_app
    
    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="draft")  # draft, scheduled, running, completed, cancelled
    
    # Statistics
    total_recipients = Column(Integer, default=0, nullable=False)
    sent_count = Column(Integer, default=0, nullable=False)
    delivered_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    read_count = Column(Integer, default=0, nullable=False)
    
    # Created by
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("User")
    recipients = relationship("CampaignRecipient", back_populates="campaign", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CommunicationCampaign(id={self.id}, name='{self.name}', status='{self.status}')>"


class CampaignRecipient(Base):
    """Campaign recipients and delivery status"""
    __tablename__ = "campaign_recipients"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("communication_campaigns.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Delivery status per channel
    email_status = Column(String(20), nullable=True)  # sent, delivered, failed, bounced, opened
    sms_status = Column(String(20), nullable=True)
    push_status = Column(String(20), nullable=True)
    in_app_status = Column(String(20), nullable=True)
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional data
    delivery_data = Column(JSON, nullable=True)  # Provider responses, tracking info
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    campaign = relationship("CommunicationCampaign", back_populates="recipients")
    user = relationship("User")
    
    def __repr__(self):
        return f"<CampaignRecipient(campaign_id={self.campaign_id}, user_id={self.user_id})>"


class ChatRoom(Base):
    """Chat rooms for group conversations"""
    __tablename__ = "chat_rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    room_type = Column(String(50), nullable=False)  # class, subject, group, support
    
    # Configuration
    is_private = Column(Boolean, default=False, nullable=False)
    max_members = Column(Integer, nullable=True)
    
    # Permissions
    allow_file_sharing = Column(Boolean, default=True, nullable=False)
    allow_member_invite = Column(Boolean, default=False, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    
    # Created by
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("User")
    members = relationship("ChatRoomMember", back_populates="room", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatRoom(id={self.id}, name='{self.name}', type='{self.room_type}')>"


class ChatRoomMember(Base):
    """Chat room membership"""
    __tablename__ = "chat_room_members"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False, default="member")  # admin, moderator, member
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_muted = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    room = relationship("ChatRoom", back_populates="members")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ChatRoomMember(room_id={self.room_id}, user_id={self.user_id}, role='{self.role}')>"


class ChatMessage(Base):
    """Chat messages within rooms"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(20), nullable=False, default="text")  # text, file, image, system
    
    # File attachments
    attachments = Column(JSON, nullable=True)  # List of file paths
    
    # Message status
    is_edited = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    room = relationship("ChatRoom", back_populates="messages")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, room_id={self.room_id}, user_id={self.user_id})>"
