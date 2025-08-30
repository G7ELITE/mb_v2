"""Initial database schema

Revision ID: 0001_init
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables for ManyBlack V2."""
    
    # Lead table
    op.create_table('lead',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('platform_user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('lang', sa.String(), nullable=False, server_default='pt-BR'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lead_platform_user_id'), 'lead', ['platform_user_id'], unique=False)
    
    # Lead Profile table
    op.create_table('lead_profile',
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('accounts', sa.JSON(), nullable=False),
        sa.Column('deposit', sa.JSON(), nullable=False),
        sa.Column('agreements', sa.JSON(), nullable=False),
        sa.Column('flags', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('lead_id')
    )
    
    # Automation Run table
    op.create_table('automation_run',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('automation_id', sa.String(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_automation_run_lead_id'), 'automation_run', ['lead_id'], unique=False)
    
    # Procedure Run table
    op.create_table('procedure_run',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('procedure_id', sa.String(), nullable=False),
        sa.Column('step', sa.String(), nullable=False),
        sa.Column('outcome', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_procedure_run_lead_id'), 'procedure_run', ['lead_id'], unique=False)
    
    # Journey Event table
    op.create_table('journey_event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_journey_event_lead_id'), 'journey_event', ['lead_id'], unique=False)
    
    # Lead Touchpoint table
    op.create_table('lead_touchpoint',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('utm_id', sa.String(), nullable=True),
        sa.Column('event', sa.String(), nullable=False),
        sa.Column('ts', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lead_touchpoint_lead_id'), 'lead_touchpoint', ['lead_id'], unique=False)
    
    # Idempotency Key table
    op.create_table('idempotency_key',
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('response', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('key')
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('idempotency_key')
    op.drop_index(op.f('ix_lead_touchpoint_lead_id'), table_name='lead_touchpoint')
    op.drop_table('lead_touchpoint')
    op.drop_index(op.f('ix_journey_event_lead_id'), table_name='journey_event')
    op.drop_table('journey_event')
    op.drop_index(op.f('ix_procedure_run_lead_id'), table_name='procedure_run')
    op.drop_table('procedure_run')
    op.drop_index(op.f('ix_automation_run_lead_id'), table_name='automation_run')
    op.drop_table('automation_run')
    op.drop_table('lead_profile')
    op.drop_index(op.f('ix_lead_platform_user_id'), table_name='lead')
    op.drop_table('lead')

