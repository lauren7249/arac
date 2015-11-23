"""empty message

Revision ID: 33f5c4ca8831
Revises: None
Create Date: 2015-11-17 13:43:33.309468

"""

# revision identifiers, used by Alembic.
revision = '33f5c4ca8831'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('prospect_wealthscore',
    sa.Column('prospect_id', sa.BigInteger(), nullable=False),
    sa.Column('wealthscore', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('prospect_id')
    )
    op.create_table('company',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=1024), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('prospect_gender',
    sa.Column('prospect_id', sa.BigInteger(), nullable=False),
    sa.Column('gender', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('prospect_id')
    )
    op.create_table('linkedin_companies',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=900), nullable=True),
    sa.Column('industry', sa.String(length=200), nullable=True),
    sa.Column('company_type', sa.String(length=200), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('pretty_url', sa.String(length=150), nullable=True),
    sa.Column('image_url', sa.String(length=900), nullable=True),
    sa.Column('founded', sa.Integer(), nullable=True),
    sa.Column('headquarters', sa.String(length=500), nullable=True),
    sa.Column('min_employees', sa.Integer(), nullable=True),
    sa.Column('max_employees', sa.Integer(), nullable=True),
    sa.Column('specialties', postgresql.ARRAY(sa.String(length=200)), nullable=True),
    sa.Column('website', sa.Text(), nullable=True),
    sa.Column('clearbit_response', postgresql.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('prospect_location',
    sa.Column('prospect_id', sa.BigInteger(), nullable=False),
    sa.Column('location_id', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('prospect_id', 'location_id')
    )
    op.create_table('customers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=1024), nullable=False),
    sa.Column('slug', sa.String(length=120), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('location',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('name', sa.Text(), nullable=True),
    sa.Column('lat', sa.Float(), nullable=True),
    sa.Column('lng', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('industry',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=1024), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('job_titles',
    sa.Column('title', sa.String(length=1024), nullable=False),
    sa.Column('indeed_salary', sa.Integer(), nullable=True),
    sa.Column('glassdoor_salary', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('title')
    )
    op.create_table('school',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=1024), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('linkedin_schools',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=900), nullable=True),
    sa.Column('pretty_url', sa.String(length=150), nullable=True),
    sa.Column('image_url', sa.String(length=900), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('first_name', sa.String(length=100), nullable=False),
    sa.Column('last_name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=False),
    sa.Column('password_hash', sa.String(length=100), nullable=False),
    sa.Column('is_admin', sa.BOOLEAN(), server_default='FALSE', nullable=False),
    sa.Column('customer_id', sa.Integer(), nullable=True),
    sa.Column('linkedin_id', sa.String(length=1024), nullable=True),
    sa.Column('linkedin_url', sa.String(length=1024), nullable=True),
    sa.Column('created', sa.Date(), nullable=True),
    sa.Column('onboarding_code', sa.String(length=40), nullable=True),
    sa.Column('json', postgresql.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
    sa.PrimaryKeyConstraint('user_id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('prospect',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(length=1024), nullable=True),
    sa.Column('name', sa.String(length=1024), nullable=True),
    sa.Column('linkedin_id', sa.String(length=1024), nullable=True),
    sa.Column('location_id', sa.Integer(), nullable=True),
    sa.Column('location_raw', sa.String(), nullable=True),
    sa.Column('lat', sa.Float(), nullable=True),
    sa.Column('lng', sa.Float(), nullable=True),
    sa.Column('image_url', sa.String(length=1024), nullable=True),
    sa.Column('headline', sa.String(length=1024), nullable=True),
    sa.Column('industry', sa.Integer(), nullable=True),
    sa.Column('industry_raw', sa.String(length=1024), nullable=True),
    sa.Column('s3_key', sa.String(length=1024), nullable=True),
    sa.Column('complete', sa.Boolean(), nullable=True),
    sa.Column('updated', sa.Date(), nullable=True),
    sa.Column('connections', sa.Integer(), nullable=True),
    sa.Column('json', postgresql.JSON(), nullable=True),
    sa.Column('google_network_search', postgresql.JSON(), nullable=True),
    sa.Column('pipl_response', postgresql.JSON(), nullable=True),
    sa.Column('pipl_contact_response', postgresql.JSON(), nullable=True),
    sa.Column('all_email_addresses', postgresql.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['industry'], ['industry.id'], ),
    sa.ForeignKeyConstraint(['location_id'], ['location.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prospect_linkedin_id'), 'prospect', ['linkedin_id'], unique=False)
    op.create_index(op.f('ix_prospect_s3_key'), 'prospect', ['s3_key'], unique=False)
    op.create_index(op.f('ix_prospect_updated'), 'prospect', ['updated'], unique=False)
    op.create_index(op.f('ix_prospect_url'), 'prospect', ['url'], unique=False)
    op.create_table('client_prospect',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('prospect_id', sa.Integer(), nullable=True),
    sa.Column('processed', sa.Boolean(), nullable=True),
    sa.Column('good', sa.Boolean(), nullable=True),
    sa.Column('created', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['prospect_id'], ['prospect.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_client_prospect_prospect_id'), 'client_prospect', ['prospect_id'], unique=False)
    op.create_index(op.f('ix_client_prospect_user_id'), 'client_prospect', ['user_id'], unique=False)
    op.create_table('education',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('school_id', sa.Integer(), nullable=True),
    sa.Column('degree', sa.String(length=200), nullable=True),
    sa.Column('prospect_id', sa.Integer(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('school_linkedin_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['prospect_id'], ['prospect.id'], ),
    sa.ForeignKeyConstraint(['school_id'], ['school.id'], ),
    sa.ForeignKeyConstraint(['school_linkedin_id'], ['linkedin_schools.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_education_prospect_id'), 'education', ['prospect_id'], unique=False)
    op.create_index(op.f('ix_education_school_id'), 'education', ['school_id'], unique=False)
    op.create_index(op.f('ix_education_school_linkedin_id'), 'education', ['school_linkedin_id'], unique=False)
    op.create_table('job',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=True),
    sa.Column('location', sa.String(length=1024), nullable=True),
    sa.Column('prospect_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=1024), nullable=True),
    sa.Column('fts_title', postgresql.TSVECTOR(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('company_linkedin_id', sa.Integer(), nullable=True),
    sa.Column('indeed_salary', sa.Integer(), nullable=True),
    sa.Column('glassdoor_salary', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['company_id'], ['company.id'], ),
    sa.ForeignKeyConstraint(['company_linkedin_id'], ['linkedin_companies.id'], ),
    sa.ForeignKeyConstraint(['prospect_id'], ['prospect.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_job_company_id'), 'job', ['company_id'], unique=False)
    op.create_index(op.f('ix_job_company_linkedin_id'), 'job', ['company_linkedin_id'], unique=False)
    op.create_index(op.f('ix_job_prospect_id'), 'job', ['prospect_id'], unique=False)
    op.create_table('managers',
    sa.Column('manager_id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('created', sa.Date(), nullable=True),
    sa.Column('json', postgresql.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('manager_id')
    )
    op.create_index(op.f('ix_managers_user_id'), 'managers', ['user_id'], unique=False)
    op.create_table('manager_users',
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('manager_id', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['manager_id'], ['managers.manager_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_manager_users_manager_id'), 'manager_users', ['manager_id'], unique=False)
    op.create_index(op.f('ix_manager_users_user_id'), 'manager_users', ['user_id'], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_manager_users_user_id'), table_name='manager_users')
    op.drop_index(op.f('ix_manager_users_manager_id'), table_name='manager_users')
    op.drop_table('manager_users')
    op.drop_index(op.f('ix_managers_user_id'), table_name='managers')
    op.drop_table('managers')
    op.drop_index(op.f('ix_job_prospect_id'), table_name='job')
    op.drop_index(op.f('ix_job_company_linkedin_id'), table_name='job')
    op.drop_index(op.f('ix_job_company_id'), table_name='job')
    op.drop_table('job')
    op.drop_index(op.f('ix_education_school_linkedin_id'), table_name='education')
    op.drop_index(op.f('ix_education_school_id'), table_name='education')
    op.drop_index(op.f('ix_education_prospect_id'), table_name='education')
    op.drop_table('education')
    op.drop_index(op.f('ix_client_prospect_user_id'), table_name='client_prospect')
    op.drop_index(op.f('ix_client_prospect_prospect_id'), table_name='client_prospect')
    op.drop_table('client_prospect')
    op.drop_index(op.f('ix_prospect_url'), table_name='prospect')
    op.drop_index(op.f('ix_prospect_updated'), table_name='prospect')
    op.drop_index(op.f('ix_prospect_s3_key'), table_name='prospect')
    op.drop_index(op.f('ix_prospect_linkedin_id'), table_name='prospect')
    op.drop_table('prospect')
    op.drop_table('users')
    op.drop_table('linkedin_schools')
    op.drop_table('school')
    op.drop_table('job_titles')
    op.drop_table('industry')
    op.drop_table('location')
    op.drop_table('customers')
    op.drop_table('prospect_location')
    op.drop_table('linkedin_companies')
    op.drop_table('prospect_gender')
    op.drop_table('company')
    op.drop_table('prospect_wealthscore')
    ### end Alembic commands ###