"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-16 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Organizations
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False, unique=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('tier', sa.String(length=50), nullable=False, server_default='free'),
        sa.Column('max_monthly_requests', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('current_period_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_organizations_slug', 'organizations', ['slug'])

    # 2. Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_users_email', 'users', ['email'])

    # 3. Workspaces
    op.create_table(
        'workspaces',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 4. Memberships
    op.create_table(
        'memberships',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='ADMIN'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 5. API Keys
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('key_prefix', sa.String(length=16), nullable=False),
        sa.Column('hashed_key', sa.String(length=64), nullable=False, unique=True),
        sa.Column('scopes', sa.String(length=255), nullable=False, server_default='proxy:all,scans:all'),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_apikeys_hash', 'api_keys', ['hashed_key'])

    # 6. Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('actor_id', sa.String(length=36), nullable=True),
        sa.Column('actor_type', sa.String(length=50), nullable=False, server_default='api_key'),
        sa.Column('request_id', sa.String(length=64), nullable=True),
        sa.Column('endpoint', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('latency_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('findings_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('categories', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('input_preview', sa.Text(), nullable=True),
        sa.Column('output_preview', sa.Text(), nullable=True),
        sa.Column('details_json', sa.Text(), nullable=True, server_default='{}'),
        sa.Column('timestamp', sa.String(length=64), nullable=False),
    )
    op.create_index('idx_audit_org', 'audit_logs', ['organization_id'])
    op.create_index('idx_audit_status', 'audit_logs', ['status'])
    op.create_index('idx_audit_timestamp', 'audit_logs', ['timestamp'])

    # 7. Policies
    op.create_table(
        'policies',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('enabled', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('action', sa.String(length=50), nullable=False, server_default='BLOCK'),
        sa.Column('severity_threshold', sa.String(length=50), nullable=False, server_default='HIGH'),
        sa.Column('config_json', sa.Text(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 8. Subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='stripe'),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('plan', sa.String(length=50), nullable=False, server_default='free'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 9. Plans
    op.create_table(
        'plans',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False, unique=True),
        sa.Column('price_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('billing_interval', sa.String(length=20), nullable=False, server_default='month'),
        sa.Column('request_limit', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('document_limit', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('features_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
    )

    # 10. Webhooks
    op.create_table(
        'webhook_endpoints',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=False),
        sa.Column('secret_hash', sa.String(length=255), nullable=False),
        sa.Column('events', sa.String(length=512), nullable=False, server_default='threat.blocked,scan.completed'),
        sa.Column('active', sa.Boolean(), server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'webhook_deliveries',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('webhook_endpoint_id', sa.String(length=36), sa.ForeignKey('webhook_endpoints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('attempt_count', sa.Integer(), server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('response_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('next_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 11. Documents & Findings
    op.create_table(
        'documents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('uploaded_by', sa.String(length=36), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='COMPLETED'),
        sa.Column('risk_score', sa.Float(), server_default='0.0'),
        sa.Column('execution_time_ms', sa.Float(), server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'findings',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', sa.String(length=36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), server_default='1.0'),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('original_snippet', sa.Text(), nullable=True),
        sa.Column('redacted_snippet', sa.Text(), nullable=True),
        sa.Column('details_json', sa.Text(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 12. Notifications & Invitations
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'invitations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='MEMBER'),
        sa.Column('token_hash', sa.String(length=64), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('invitations')
    op.drop_table('notifications')
    op.drop_table('findings')
    op.drop_table('documents')
    op.drop_table('webhook_deliveries')
    op.drop_table('webhook_endpoints')
    op.drop_table('plans')
    op.drop_table('subscriptions')
    op.drop_table('policies')
    op.drop_table('audit_logs')
    op.drop_table('api_keys')
    op.drop_table('memberships')
    op.drop_table('workspaces')
    op.drop_table('users')
    op.drop_table('organizations')
