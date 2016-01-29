"""empty message

Revision ID: 48b7bc65ff75
Revises: None
Create Date: 2016-01-29 10:30:11.908372

"""

# revision identifiers, used by Alembic.
revision = '48b7bc65ff75'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('client_prospect', sa.Column('sources', postgresql.JSONB(), nullable=True))
    op.add_column('users', sa.Column('account_sources', postgresql.JSONB(), nullable=True))
    op.add_column('users', sa.Column('contacts_from_gmail', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('contacts_from_linkedin', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('contacts_from_windowslive', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('contacts_from_yahoo', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('p200_approved', sa.BOOLEAN(), nullable=True))
    op.add_column('users', sa.Column('p200_submitted_to_manager', sa.BOOLEAN(), nullable=True))
    op.add_column('users', sa.Column('prospect_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'users', 'prospect', ['prospect_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_column('users', 'prospect_id')
    op.drop_column('users', 'p200_submitted_to_manager')
    op.drop_column('users', 'p200_approved')
    op.drop_column('users', 'contacts_from_yahoo')
    op.drop_column('users', 'contacts_from_windowslive')
    op.drop_column('users', 'contacts_from_linkedin')
    op.drop_column('users', 'contacts_from_gmail')
    op.drop_column('users', 'account_sources')
    op.drop_column('client_prospect', 'sources')
    ### end Alembic commands ###
