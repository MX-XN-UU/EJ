"""add is_risky to questions

Revision ID: 4f3cc1b23172
Revises: fce828d825fe
Create Date: 2025-05-08 09:23:43.213212

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f3cc1b23172'
down_revision: Union[str, None] = 'fce828d825fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('questions', sa.Column('is_risky', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('questions', 'is_risky')
    # ### end Alembic commands ###
