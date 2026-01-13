"""add SUPERADMIN to role enum

Revision ID: e43a88e57eb6
Revises: 50855d71ec7d
Create Date: 2026-01-13 17:55:06.136113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e43a88e57eb6'
down_revision: Union[str, Sequence[str], None] = '50855d71ec7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE role ADD VALUE IF NOT EXISTS 'SUPERADMIN';")


def downgrade():
    pass
