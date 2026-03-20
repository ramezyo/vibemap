"""Create tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Enable PostGIS
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    
    # Create vibe_anchors table
    op.create_table(
        'vibe_anchors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lon', sa.Float(), nullable=False),
        sa.Column('geom', geoalchemy2.Geometry('POINT', srid=4326)),
        sa.Column('social_energy', sa.Float(), default=0.5),
        sa.Column('creative_energy', sa.Float(), default=0.5),
        sa.Column('commercial_energy', sa.Float(), default=0.5),
        sa.Column('residential_energy', sa.Float(), default=0.5),
        sa.Column('genesis', sa.DateTime(), default=sa.func.now()),
        sa.Column('last_pulse', sa.DateTime(), default=sa.func.now()),
        sa.Column('checkin_count', sa.Integer(), default=0),
        sa.Column('properties', postgresql.JSONB(), default=dict),
    )
    
    # Create indexes for vibe_anchors
    op.create_index('idx_vibe_anchors_geom', 'vibe_anchors', ['geom'])
    op.create_index('idx_vibe_anchors_location', 'vibe_anchors', ['lat', 'lon'])
    op.create_index('idx_vibe_anchors_social_energy', 'vibe_anchors', ['social_energy'])
    
    # Create agent_checkins table
    op.create_table(
        'agent_checkins',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', sa.String(255), nullable=False, index=True),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lon', sa.Float(), nullable=False),
        sa.Column('geom', geoalchemy2.Geometry('POINT', srid=4326)),
        sa.Column('accuracy_meters', sa.Float()),
        sa.Column('social_reading', sa.Float()),
        sa.Column('creative_reading', sa.Float()),
        sa.Column('commercial_reading', sa.Float()),
        sa.Column('residential_reading', sa.Float()),
        sa.Column('timestamp', sa.DateTime(), default=sa.func.now(), index=True),
        sa.Column('activity_type', sa.String(50)),
        sa.Column('sensory_payload', postgresql.JSONB(), default=dict),
        sa.Column('anchor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vibe_anchors.id')),
    )
    
    # Create indexes for agent_checkins
    op.create_index('idx_agent_checkins_geom', 'agent_checkins', ['geom'])
    op.create_index('idx_agent_checkins_agent_timestamp', 'agent_checkins', ['agent_id', 'timestamp'])
    op.create_index('idx_agent_checkins_location', 'agent_checkins', ['lat', 'lon'])
    
    # Create vibe_pulses table
    op.create_table(
        'vibe_pulses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('anchor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vibe_anchors.id'), nullable=False),
        sa.Column('social_energy', sa.Float()),
        sa.Column('creative_energy', sa.Float()),
        sa.Column('commercial_energy', sa.Float()),
        sa.Column('residential_energy', sa.Float()),
        sa.Column('checkin_count', sa.Integer()),
        sa.Column('unique_agents', sa.Integer()),
        sa.Column('timestamp', sa.DateTime(), default=sa.func.now(), index=True),
    )
    
    # Create index for vibe_pulses
    op.create_index('idx_vibe_pulses_anchor_time', 'vibe_pulses', ['anchor_id', 'timestamp'])


def downgrade():
    op.drop_table('vibe_pulses')
    op.drop_table('agent_checkins')
    op.drop_table('vibe_anchors')
