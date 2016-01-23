"""empty message

Revision ID: a9180d13c47
Revises: 41a190f59989
Create Date: 2016-01-22 17:47:00.097691

"""

# revision identifiers, used by Alembic.
revision = 'a9180d13c47'
down_revision = '41a190f59989'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('client_prospect', sa.Column('sources', postgresql.JSONB(), nullable=True))
    op.add_column('users', sa.Column('contacts_from_gmail', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('contacts_from_linkedin', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('contacts_from_windowslive', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('contacts_from_yahoo', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'contacts_from_yahoo')
    op.drop_column('users', 'contacts_from_windowslive')
    op.drop_column('users', 'contacts_from_linkedin')
    op.drop_column('users', 'contacts_from_gmail')
    op.drop_column('client_prospect', 'sources')
    ### end Alembic commands ###