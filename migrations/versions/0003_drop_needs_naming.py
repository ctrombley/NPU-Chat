"""drop needs_naming column from chats

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-27

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('chats') as batch_op:
        batch_op.drop_column('needs_naming')


def downgrade():
    with op.batch_alter_table('chats') as batch_op:
        batch_op.add_column(
            sa.Column('needs_naming', sa.Boolean(), nullable=True, server_default='0')
        )
