"""create dues tables

Revision ID: 82e45c1409f5
Revises: f711ec857a1e
Create Date: 2026-01-13 08:20:53

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50855d71ec7d'
down_revision: Union[str, Sequence[str], None] = 'f711ec857a1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'dues_charges',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('period', sa.String(length=7), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('period', name='uq_dues_charges_period'),
    )

    op.create_table(
        'dues_payments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('charge_id', sa.UUID(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('method', sa.String(length=20), nullable=False),
        sa.Column('memo', sa.String(length=255), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['charge_id'], ['dues_charges.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('ix_dues_payments_user_id', 'dues_payments', ['user_id'])
    op.create_index('ix_dues_payments_charge_id', 'dues_payments', ['charge_id'])


def downgrade() -> None:
    op.drop_index('ix_dues_payments_charge_id', table_name='dues_payments')
    op.drop_index('ix_dues_payments_user_id', table_name='dues_payments')
    op.drop_table('dues_payments')
    op.drop_table('dues_charges')
