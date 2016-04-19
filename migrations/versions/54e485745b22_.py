"""empty message

Revision ID: 54e485745b22
Revises: None
Create Date: 2016-04-19 16:28:37.494354

"""

# revision identifiers, used by Alembic.
revision = '54e485745b22'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('prospect', sa.Column('instagram', sa.String(length=500), nullable=True))
    op.add_column('prospect', sa.Column('primary_emails', postgresql.JSONB(), nullable=True))
    op.add_column('users', sa.Column('_statistics_p200', postgresql.JSONB(), nullable=True))
    op.add_column('users', sa.Column('all_states', postgresql.JSONB(), nullable=True))
    op.add_column('users', sa.Column('contacts_from_icloud', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('hiring_screen_started', sa.BOOLEAN(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'hiring_screen_started')
    op.drop_column('users', 'contacts_from_icloud')
    op.drop_column('users', 'all_states')
    op.drop_column('users', '_statistics_p200')
    op.drop_column('prospect', 'primary_emails')
    op.drop_column('prospect', 'instagram')
    ### end Alembic commands ###
