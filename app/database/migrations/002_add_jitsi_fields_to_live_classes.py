"""Add Jitsi Meet fields to live classes

Revision ID: 002
Revises: 001
Create Date: 2025-08-25 06:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Add Jitsi Meet fields to live_classes table
    op.add_column('live_classes', sa.Column('jitsi_room_name', sa.String(255), nullable=True))
    op.add_column('live_classes', sa.Column('jitsi_meeting_url', sa.String(500), nullable=True))
    op.add_column('live_classes', sa.Column('jitsi_meeting_id', sa.String(255), nullable=True))
    op.add_column('live_classes', sa.Column('jitsi_settings', sa.JSON(), nullable=True))
    op.add_column('live_classes', sa.Column('jitsi_token', sa.Text(), nullable=True))
    op.add_column('live_classes', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('live_classes', sa.Column('max_participants', sa.Integer(), nullable=False, server_default='50'))
    op.add_column('live_classes', sa.Column('is_password_protected', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('live_classes', sa.Column('meeting_password', sa.String(100), nullable=True))
    op.add_column('live_classes', sa.Column('allow_join_before_host', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('live_classes', sa.Column('mute_upon_entry', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('live_classes', sa.Column('video_off_upon_entry', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('live_classes', sa.Column('enable_chat', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('live_classes', sa.Column('enable_whiteboard', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('live_classes', sa.Column('enable_screen_sharing', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('live_classes', sa.Column('enable_recording', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('live_classes', sa.Column('enable_breakout_rooms', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('live_classes', sa.Column('enable_polls', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('live_classes', sa.Column('enable_reactions', sa.Boolean(), nullable=False, server_default='1'))
    
    # Create index for jitsi_room_name
    op.create_index(op.f('ix_live_classes_jitsi_room_name'), 'live_classes', ['jitsi_room_name'], unique=True)
    
    # Add Jitsi Meet fields to class_attendance table
    op.add_column('class_attendance', sa.Column('jitsi_participant_id', sa.String(255), nullable=True))
    op.add_column('class_attendance', sa.Column('jitsi_join_token', sa.Text(), nullable=True))
    op.add_column('class_attendance', sa.Column('connection_quality', sa.String(50), nullable=True))
    op.add_column('class_attendance', sa.Column('device_info', sa.JSON(), nullable=True))


def downgrade():
    # Remove indexes
    op.drop_index(op.f('ix_live_classes_jitsi_room_name'), table_name='live_classes')
    
    # Remove columns from live_classes table
    op.drop_column('live_classes', 'enable_reactions')
    op.drop_column('live_classes', 'enable_polls')
    op.drop_column('live_classes', 'enable_breakout_rooms')
    op.drop_column('live_classes', 'enable_recording')
    op.drop_column('live_classes', 'enable_screen_sharing')
    op.drop_column('live_classes', 'enable_whiteboard')
    op.drop_column('live_classes', 'enable_chat')
    op.drop_column('live_classes', 'video_off_upon_entry')
    op.drop_column('live_classes', 'mute_upon_entry')
    op.drop_column('live_classes', 'allow_join_before_host')
    op.drop_column('live_classes', 'meeting_password')
    op.drop_column('live_classes', 'is_password_protected')
    op.drop_column('live_classes', 'max_participants')
    op.drop_column('live_classes', 'description')
    op.drop_column('live_classes', 'jitsi_token')
    op.drop_column('live_classes', 'jitsi_settings')
    op.drop_column('live_classes', 'jitsi_meeting_id')
    op.drop_column('live_classes', 'jitsi_meeting_url')
    op.drop_column('live_classes', 'jitsi_room_name')
    
    # Remove columns from class_attendance table
    op.drop_column('class_attendance', 'device_info')
    op.drop_column('class_attendance', 'connection_quality')
    op.drop_column('class_attendance', 'jitsi_join_token')
    op.drop_column('class_attendance', 'jitsi_participant_id')
