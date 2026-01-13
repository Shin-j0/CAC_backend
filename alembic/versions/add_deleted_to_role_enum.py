"""add DELETED to role enum 

Revision ID: 94fa9872b891
Revises: 64ac096e193a
Create Date: 2026-01-13 22:06:21.186283

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94fa9872b891'
down_revision: Union[str, Sequence[str], None] = '64ac096e193a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() :
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE role ADD VALUE IF NOT EXISTS 'DELETED';")


def downgrade() -> None:
    """Downgrade schema."""
    pass
