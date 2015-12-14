"""empty message

Revision ID: 5096425b46bd
Revises: 22337b9707bf
Create Date: 2015-12-13 07:24:02.640885

"""

# revision identifiers, used by Alembic.
revision = '5096425b46bd'
down_revision = '22337b9707bf'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('client_prospect', 'lead_score',
               existing_type=sa.INTEGER(),
               nullable=True)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('client_prospect', 'lead_score',
               existing_type=sa.INTEGER(),
               nullable=False)
    ### end Alembic commands ###
