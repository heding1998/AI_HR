"""add applications and talent_pool

Revision ID: 3d9f1a7c2b8e
Revises: 65fd7bb00c78
Create Date: 2026-10-16 22:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d9f1a7c2b8e'
down_revision: Union[str, Sequence[str], None] = '65fd7bb00c78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('resume_id', sa.Integer(), nullable=False),
        sa.Column('candidate_name', sa.String(length=128), nullable=False),
        sa.Column('candidate_contact', sa.String(length=128), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_applications_job_id', 'applications', ['job_id'])
    op.create_index('ix_applications_resume_id', 'applications', ['resume_id'], unique=True)

    op.create_table(
        'talent_pool',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('contact', sa.String(length=128), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('tier', sa.String(length=32), nullable=False),
        sa.Column('resume_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'contact', name='uq_talent_pool_name_contact'),
    )
    op.create_index('ix_talent_pool_contact', 'talent_pool', ['contact'])
    op.create_index('ix_talent_pool_name', 'talent_pool', ['name'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_talent_pool_name', table_name='talent_pool')
    op.drop_index('ix_talent_pool_contact', table_name='talent_pool')
    op.drop_table('talent_pool')
    op.drop_index('ix_applications_resume_id', table_name='applications')
    op.drop_index('ix_applications_job_id', table_name='applications')
    op.drop_table('applications')
