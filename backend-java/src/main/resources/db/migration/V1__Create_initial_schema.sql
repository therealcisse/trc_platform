-- Clean up existing data for fresh start
DROP TABLE IF EXISTS request_logs CASCADE;
DROP TABLE IF EXISTS billing_periods CASCADE;
DROP TABLE IF EXISTS api_tokens CASCADE;
DROP TABLE IF EXISTS invite_codes CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS settings CASCADE;
DROP TYPE IF EXISTS payment_status_type CASCADE;

-- Create enum types
CREATE TYPE payment_status_type AS ENUM ('pending', 'paid', 'overdue', 'waived');
CREATE TYPE request_logs_status_type AS ENUM ('SUCCESS', 'ERROR');

-- Users
create table if not exists users (
  id uuid primary key,
  email varchar(255) not null unique,
  password_hash varchar(255) not null,
  is_active boolean not null default true,
  is_staff boolean not null default false,
  email_verified_at timestamp with time zone null,
  date_joined timestamp with time zone not null,
  user_accepted_terms boolean not null default false,
  user_acknowledged_disclaimer boolean not null default false,
  version bigint,
  constraint chk_email_not_blank check (length(email) > 0)
);

-- Settings singleton
create table if not exists settings (
  id bigint primary key,
  cost_per_request_cents integer not null default 100,
  openai_model varchar(255),
  openai_timeout_s integer not null default 30,
  app_domain varchar(1024),
  updated_at timestamp with time zone not null
);

-- API tokens
create table if not exists api_tokens (
  id uuid primary key,
  user_id uuid not null references users(id),
  token_hash varchar(255) not null unique,
  token_prefix varchar(64) not null,
  name varchar(255) not null,
  created_at timestamp with time zone not null,
  last_used_at timestamp with time zone null,
  expires_at timestamp with time zone null,
  revoked_at timestamp with time zone null
);

-- Optimize API token lookup by hash
create index if not exists idx_api_tokens_token_hash on api_tokens(token_hash);

-- Billing periods
create table if not exists billing_periods (
  id uuid primary key,
  user_id uuid not null references users(id),
  period_start date not null,
  period_end date not null,
  total_requests integer not null default 0,
  total_cost_cents integer not null default 0,
  is_current boolean not null default false,
  payment_status payment_status_type not null default 'pending',
  paid_at timestamp with time zone null,
  paid_amount_cents integer,
  payment_reference varchar(255),
  notes text,
  version bigint
);

create index if not exists idx_user_period on billing_periods(user_id, period_start);
create index if not exists idx_current_period on billing_periods(is_current);
create index if not exists idx_billing_payment_status on billing_periods(payment_status);

-- Request logs
create table if not exists request_logs (
  id uuid primary key,
  user_id uuid not null references users(id),
  token_id uuid null references api_tokens(id),
  billing_period_id uuid null references billing_periods(id),
  service varchar(255) not null,
  request_ts timestamp with time zone not null,
  duration_ms integer not null,
  request_bytes integer not null,
  response_bytes integer not null,
  status request_logs_status_type not null,
  error_code varchar(50) null,
  request_id uuid not null,
  flow_id varchar(255) null,
  result text null
);

create index if not exists idx_user_timestamp on request_logs(user_id, request_ts);
create index if not exists idx_request_ts on request_logs(request_ts);
create index if not exists idx_request_id on request_logs(request_id);
create index if not exists idx_flow_id on request_logs(flow_id);

-- Invite codes
create table if not exists invite_codes (
  id uuid primary key,
  code varchar(32) not null unique,
  is_active boolean not null default true,
  expires_at timestamp with time zone null,
  created_at timestamp with time zone not null,
  used_at timestamp with time zone null,
  used_by_user_id uuid null references users(id),
  created_by_user_id uuid null references users(id)
);

create index if not exists idx_code on invite_codes(code);
create index if not exists idx_invite_created_by on invite_codes(created_by_user_id);



-- Insert default settings
INSERT INTO settings (id, cost_per_request_cents, openai_model, openai_timeout_s, updated_at) VALUES
    (1, 100, 'gpt-4.1-mini-2025-04-14', 30, NOW());

