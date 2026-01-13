"""add SUPERADMIN to role enum (fix)

Revision ID: 93a16b0f4d5c
Revises: e43a88e57eb6
Create Date: 2026-01-13 18:04:23.886158

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93a16b0f4d5c'
down_revision: Union[str, Sequence[str], None] = 'e43a88e57eb6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() :
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE role ADD VALUE IF NOT EXISTS 'SUPERADMIN';")


def downgrade():
    pass
