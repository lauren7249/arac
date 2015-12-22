"""empty message

Revision ID: 4f099ffa71cf
Revises: 14ddbee97789
Create Date: 2015-12-11 19:28:32.108583

"""

# revision identifiers, used by Alembic.
revision = '4f099ffa71cf'
down_revision = '14ddbee97789'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('prospect', sa.Column('dob_max_year', sa.Integer(), nullable=True))
    op.add_column('prospect', sa.Column('dob_min_year', sa.Integer(), nullable=True))
    op.drop_column('prospect', 'dob_max')
    op.drop_column('prospect', 'dob_min')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('prospect', sa.Column('dob_min', sa.DATE(), autoincrement=False, nullable=True))
    op.add_column('prospect', sa.Column('dob_max', sa.DATE(), autoincrement=False, nullable=True))
    op.drop_column('prospect', 'dob_min_year')
    op.drop_column('prospect', 'dob_max_year')
    ### end Alembic commands ###