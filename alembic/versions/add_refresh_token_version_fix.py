"""add refresh_token_version_fix

Revision ID: e2509e68c5d5
Revises: 516fa229371c
Create Date: 2026-01-14 01:09:23.548137

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2509e68c5d5'
down_revision: Union[str, Sequence[str], None] = '516fa229371c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("refresh_token_version", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.alter_column("users", "refresh_token_version", server_default=None)

def downgrade():
    op.drop_column("users", "refresh_token_version")
