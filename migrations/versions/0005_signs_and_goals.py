"""rename templates to signs, add aspects and goal columns

Revision ID: 0005
Revises: 0004
Create Date: 2026-02-28

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table('templates', 'signs')

    with op.batch_alter_table('signs') as batch_op:
        batch_op.add_column(sa.Column('values', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('interests', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('default_goal', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('aspects', sa.Text(), nullable=True))

    with op.batch_alter_table('chats') as batch_op:
        batch_op.alter_column('template_id', new_column_name='sign_id')
        batch_op.add_column(sa.Column('goal', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('chats') as batch_op:
        batch_op.drop_column('goal')
        batch_op.alter_column('sign_id', new_column_name='template_id')

    with op.batch_alter_table('signs') as batch_op:
        batch_op.drop_column('aspects')
        batch_op.drop_column('default_goal')
        batch_op.drop_column('interests')
        batch_op.drop_column('values')

    op.rename_table('signs', 'templates')
