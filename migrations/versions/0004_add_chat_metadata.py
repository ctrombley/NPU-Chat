"""add metadata column to chats

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-27

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('chats') as batch_op:
        batch_op.add_column(sa.Column('metadata', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('chats') as batch_op:
        batch_op.drop_column('metadata')
