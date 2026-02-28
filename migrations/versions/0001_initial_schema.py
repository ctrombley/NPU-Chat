"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-02-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'chats',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('emoji', sa.String(10), server_default=''),
        sa.Column('template_id', sa.String(50), server_default='default'),
        sa.Column('needs_naming', sa.Boolean(), server_default=sa.text('0')),
        sa.Column('is_favorite', sa.Boolean(), server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime()),
    )

    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('chat_id', sa.String(50), sa.ForeignKey('chats.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
    )

    op.create_table(
        'templates',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('prefix', sa.Text(), nullable=False),
        sa.Column('postfix', sa.Text(), nullable=False),
    )


def downgrade():
    op.drop_table('templates')
    op.drop_table('messages')
    op.drop_table('chats')
