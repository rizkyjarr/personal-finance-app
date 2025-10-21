"""add other_category to transactions

Revision ID: 0001_add_other_category
Revises: 
Create Date: 2025-10-21
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_other_category'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add other_category column to transactions
    op.add_column('transactions', sa.Column('other_category', sa.String(length=100), nullable=True))


def downgrade():
    # Remove other_category column
    op.drop_column('transactions', 'other_category')
