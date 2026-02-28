"""add role column to messages

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('messages') as batch_op:
        batch_op.add_column(
            sa.Column('role', sa.String(20), nullable=False, server_default='system')
        )

    # Data migration: set role based on content prefix
    op.execute("UPDATE messages SET role='user' WHERE content LIKE 'User: %'")
    op.execute("UPDATE messages SET role='assistant' WHERE content LIKE 'Assistant: %'")

    # Strip prefixes from content
    op.execute("UPDATE messages SET content = SUBSTR(content, 7) WHERE role='user'")
    op.execute("UPDATE messages SET content = SUBSTR(content, 12) WHERE role='assistant'")


def downgrade():
    # Re-add prefixes
    op.execute("UPDATE messages SET content = 'User: ' || content WHERE role='user'")
    op.execute("UPDATE messages SET content = 'Assistant: ' || content WHERE role='assistant'")

    with op.batch_alter_table('messages') as batch_op:
        batch_op.drop_column('role')
