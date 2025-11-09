# Task 2: Database Schema and Migrations

## Description
Create SQLx database migrations that replicate the Java backend's PostgreSQL schema. This task ensures complete database compatibility while leveraging SQLx's compile-time query validation capabilities.

## Acceptance Criteria
1. ✅ Create SQLx migration files matching the Java schema exactly
2. ✅ Implement all custom enum types (payment_status_type, request_logs_status_type)
3. ✅ Create all tables with proper constraints and indexes
4. ✅ Set up SQLx migration management system
5. ✅ Verify migrations can be applied successfully
6. ✅ Create database module structure in infrastructure layer
7. ✅ Test database connectivity and basic operations

## Prerequisites
- **Task 1**: Project Setup (completed)

## Technical Implementation

### Step 1: Create Migration Directory Structure
```bash
# In backend-rs/
# migrations/ directory should already exist from Task 1
```

### Step 2: Create Initial Schema Migration

#### migrations/V1__Create_initial_schema.sql
```sql
-- Clean up existing data for fresh start
DROP TABLE IF EXISTS request_logs CASCADE;
DROP TABLE IF EXISTS billing_periods CASCADE;
DROP TABLE IF EXISTS api_tokens CASCADE;
DROP TABLE IF EXISTS invite_codes CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS settings CASCADE;
DROP TYPE IF EXISTS payment_status_type CASCADE;
DROP TYPE IF EXISTS request_logs_status_type CASCADE;

-- Create enum types
CREATE TYPE payment_status_type AS ENUM ('pending', 'paid', 'overdue', 'waived');
CREATE TYPE request_logs_status_type AS ENUM ('SUCCESS', 'ERROR');

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email varchar(255) NOT NULL UNIQUE,
  password_hash varchar(255) NOT NULL,
  is_active boolean NOT NULL DEFAULT true,
  is_staff boolean NOT NULL DEFAULT false,
  email_verified_at timestamp with time zone null,
  date_joined timestamp with time zone NOT NULL DEFAULT now(),
  user_accepted_terms boolean NOT NULL DEFAULT false,
  user_acknowledged_disclaimer boolean NOT NULL DEFAULT false,
  version bigint,
  constraint chk_email_not_blank check (length(email) > 0)
);

-- Settings singleton table
CREATE TABLE IF NOT EXISTS settings (
  id bigint PRIMARY KEY DEFAULT 1,
  cost_per_request_cents integer NOT NULL DEFAULT 100,
  openai_model varchar(255),
  openai_timeout_s integer NOT NULL DEFAULT 30,
  app_domain varchar(1024),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT single_row CHECK (id = 1)
);

-- API tokens table
CREATE TABLE IF NOT EXISTS api_tokens (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL references users(id) ON DELETE CASCADE,
  token_hash varchar(255) NOT NULL UNIQUE,
  token_prefix varchar(64) NOT NULL,
  name varchar(255) NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  last_used_at timestamp with time zone null,
  expires_at timestamp with time zone null,
  revoked_at timestamp with time zone null
);

-- Invite codes table
CREATE TABLE IF NOT EXISTS invite_codes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code varchar(32) NOT NULL UNIQUE,
  is_active boolean NOT NULL DEFAULT true,
  expires_at timestamp with time zone null,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  used_at timestamp with time zone null,
  used_by_user_id uuid references users(id),
  created_by_user_id uuid references users(id)
);

-- Billing periods table
CREATE TABLE IF NOT EXISTS billing_periods (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL references users(id) ON DELETE CASCADE,
  period_start date NOT NULL,
  period_end date NOT NULL,
  total_requests integer NOT NULL DEFAULT 0,
  total_cost_cents integer NOT NULL DEFAULT 0,
  is_current boolean NOT NULL DEFAULT false,
  payment_status payment_status_type NOT NULL DEFAULT 'pending',
  paid_at timestamp with time zone null,
  paid_amount_cents integer null,
  payment_reference varchar(255) null,
  notes text null,
  version bigint
);

-- Request logs table
CREATE TABLE IF NOT EXISTS request_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL references users(id) ON DELETE CASCADE,
  token_id uuid references api_tokens(id) ON DELETE CASCADE,
  billing_period_id uuid references billing_periods(id) ON DELETE CASCADE,
  service varchar(255) NOT NULL,
  request_ts timestamp with time zone NOT NULL DEFAULT now(),
  duration_ms integer NOT NULL,
  request_bytes integer NOT NULL,
  response_bytes integer NOT NULL,
  status request_logs_status_type NOT NULL,
  error_code varchar(50) null,
  request_id uuid NOT NULL DEFAULT gen_random_uuid(),
  flow_id varchar(255) null,
  result text null
);

-- Insert default settings row
INSERT INTO settings (id, cost_per_request_cents, openai_model, openai_timeout_s, updated_at)
VALUES (1, 100, 'gpt-4.1-mini-2025-04-14', 30, now())
ON CONFLICT (id) DO NOTHING;
```

#### migrations/V2__Add_performance_indexes.sql
```sql
-- Performance indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active_email_verified ON users(is_active, email_verified_at);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_is_staff ON users(is_staff);
CREATE INDEX IF NOT EXISTS idx_users_staff_active ON users(is_staff, is_active);

-- Performance indexes for api_tokens table
CREATE INDEX IF NOT EXISTS idx_api_tokens_token_hash ON api_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_api_tokens_user_id ON api_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_api_tokens_last_used ON api_tokens(last_used_at) WHERE last_used_at IS NOT NULL;

-- Performance indexes for invite_codes table
CREATE INDEX IF NOT EXISTS idx_invite_codes_code ON invite_codes(code);
CREATE INDEX IF NOT EXISTS idx_invite_codes_active ON invite_codes(is_active);
CREATE INDEX IF NOT EXISTS idx_invite_codes_expires ON invite_codes(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_invite_codes_created_by ON invite_codes(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_invite_codes_used_by ON invite_codes(used_by_user_id);

-- Performance indexes for billing_periods table
CREATE INDEX IF NOT EXISTS idx_billing_periods_user_id ON billing_periods(user_id);
CREATE INDEX IF NOT EXISTS idx_billing_periods_current ON billing_periods(is_current) WHERE is_current = true;
CREATE INDEX IF NOT EXISTS idx_user_period ON billing_periods(user_id, period_start);
CREATE INDEX IF NOT EXISTS idx_billing_payment_status ON billing_periods(payment_status);

-- Performance indexes for request_logs table
CREATE INDEX IF NOT EXISTS idx_request_logs_user_id ON request_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_request_logs_token_id ON request_logs(token_id);
CREATE INDEX IF NOT EXISTS idx_request_logs_billing_period_id ON request_logs(billing_period_id);
CREATE INDEX IF NOT EXISTS idx_request_logs_request_ts ON request_logs(request_ts);
CREATE INDEX IF NOT EXISTS idx_request_logs_service ON request_logs(service);
CREATE INDEX IF NOT EXISTS idx_request_logs_status ON request_logs(status);
CREATE INDEX IF NOT EXISTS idx_user_timestamp ON request_logs(user_id, request_ts);
CREATE INDEX IF NOT EXISTS idx_flow_id ON request_logs(flow_id) WHERE flow_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_request_id ON request_logs(request_id);

-- Unique constraint for billing periods per user per month
CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_periods_unique_user_month
ON billing_periods(user_id, period_start);
```

#### migrations/V3__Add_audit_triggers.sql
```sql
-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for settings table
DROP TRIGGER IF EXISTS update_settings_updated_at ON settings;
CREATE TRIGGER update_settings_updated_at
    BEFORE UPDATE ON settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Step 3: Create Database Module Structure

#### src/infrastructure/database/mod.rs
```rust
//! Database layer with SQLx integration

pub mod connection;
pub mod models;
pub mod repositories;
pub mod migrations;

pub use connection::*;
pub use models::*;
pub use repositories::*;
pub use migrations::*;

use sqlx::PgPool;
use std::sync::Arc;

/// Database connection pool wrapper
#[derive(Clone)]
pub struct Database {
    pool: Arc<PgPool>,
}

impl Database {
    pub fn new(pool: PgPool) -> Self {
        Self {
            pool: Arc::new(pool),
        }
    }

    pub fn pool(&self) -> &PgPool {
        &self.pool
    }

    /// Health check for database connectivity
    pub async fn health_check(&self) -> Result<(), sqlx::Error> {
        sqlx::query("SELECT 1")
            .fetch_one(self.pool.as_ref())
            .await?;
        Ok(())
    }
}
```

#### src/infrastructure/database/connection.rs
```rust
//! Database connection management

use sqlx::{PgPool, postgres::PgPoolOptions};
use std::time::Duration;
use crate::config::DatabaseSettings;
use crate::AppError;

/// Create database connection pool with optimized settings
pub async fn create_pool(settings: &DatabaseSettings) -> Result<sqlx::PgPool, AppError> {
    // Configure connection pool with Hikari-inspired settings
    let pool = PgPoolOptions::new()
        .max_connections(settings.max_connections)
        .min_connections(5)
        .acquire_timeout(Duration::from_secs(10))
        .idle_timeout(Duration::from_secs(300))
        .max_lifetime(Duration::from_secs(600))
        .test_before_acquire(true)
        .connect(&settings.url)
        .await
        .map_err(|e| AppError::Database(e))?;

    // Test the connection
    pool.ping()
        .await
        .map_err(|e| AppError::Database(e))?;

    tracing::info!("Database connection pool created successfully");
    Ok(pool)
}

/// Run database migrations
pub async fn run_migrations(pool: &PgPool) -> Result<(), AppError> {
    sqlx::migrate!("./migrations")
        .run(pool)
        .await
        .map_err(|e| AppError::Database(e))?;

    tracing::info!("Database migrations completed successfully");
    Ok(())
}
```

#### src/infrastructure/database/models/mod.rs
```rust
//! Database model definitions using SQLx query macros

pub mod users;
pub mod api_tokens;
pub mod billing_periods;
pub mod request_logs;
pub mod invite_codes;
pub mod settings;

pub use users::*;
pub use api_tokens::*;
pub use billing_periods::*;
pub use request_logs::*;
pub use invite_codes::*;
pub use settings::*;
```

#### src/infrastructure/database/models/users.rs
```rust
//! User model with SQLx mappings

use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use chrono::{DateTime, Utc};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct User {
    pub id: Uuid,
    pub email: String,
    pub password_hash: String,
    pub is_active: bool,
    pub is_staff: bool,
    pub email_verified_at: Option<DateTime<Utc>>,
    pub date_joined: DateTime<Utc>,
    pub user_accepted_terms: bool,
    pub user_acknowledged_disclaimer: bool,
    pub version: Option<i64>,
}

impl User {
    pub fn is_email_verified(&self) -> bool {
        self.email_verified_at.is_some()
    }

    pub fn has_accepted_terms(&self) -> bool {
        self.user_accepted_terms
    }

    pub fn has_acknowledged_disclaimer(&self) -> bool {
        self.user_acknowledged_disclaimer
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CreateUser {
    pub email: String,
    pub password_hash: String,
    pub is_active: bool,
    pub is_staff: bool,
    pub user_accepted_terms: bool,
    pub user_acknowledged_disclaimer: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UpdateUser {
    pub email: Option<String>,
    pub password_hash: Option<String>,
    pub is_active: Option<bool>,
    pub is_staff: Option<bool>,
    pub email_verified_at: Option<DateTime<Utc>>,
    pub user_accepted_terms: Option<bool>,
    pub user_acknowledged_disclaimer: Option<bool>,
    pub version: i64,
}
```

#### src/infrastructure/database/models/api_tokens.rs
```rust
//! API Token model

use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use chrono::{DateTime, Utc};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct ApiToken {
    pub id: Uuid,
    pub user_id: Uuid,
    pub token_hash: String,
    pub token_prefix: String,
    pub name: String,
    pub created_at: DateTime<Utc>,
    pub last_used_at: Option<DateTime<Utc>>,
    pub expires_at: Option<DateTime<Utc>>,
    pub revoked_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CreateApiToken {
    pub user_id: Uuid,
    pub token_hash: String,
    pub token_prefix: String,
    pub name: String,
    pub expires_at: Option<DateTime<Utc>>,
}

impl ApiToken {
    pub fn is_valid(&self) -> bool {
        // Check if token is not revoked and not expired
        let now = Utc::now();

        if let Some(revoked_at) = self.revoked_at {
            if revoked_at <= now {
                return false;
            }
        }

        if let Some(expires_at) = self.expires_at {
            if expires_at <= now {
                return false;
            }
        }

        true
    }
}
```

#### src/infrastructure/database/models/billing_periods.rs
```rust
//! Billing period model

use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use chrono::{DateTime, Utc, NaiveDate};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "payment_status_type")]
pub enum PaymentStatus {
    #[serde(rename = "pending")]
    #[sqlx(rename = "pending")]
    Pending,
    #[serde(rename = "paid")]
    #[sqlx(rename = "paid")]
    Paid,
    #[serde(rename = "overdue")]
    #[sqlx(rename = "overdue")]
    Overdue,
    #[serde(rename = "waived")]
    #[sqlx(rename = "waived")]
    Waived,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct BillingPeriod {
    pub id: Uuid,
    pub user_id: Uuid,
    pub period_start: NaiveDate,
    pub period_end: NaiveDate,
    pub total_requests: i32,
    pub total_cost_cents: i32,
    pub is_current: bool,
    pub payment_status: PaymentStatus,
    pub paid_at: Option<DateTime<Utc>>,
    pub paid_amount_cents: Option<i32>,
    pub payment_reference: Option<String>,
    pub notes: Option<String>,
    pub version: Option<i64>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CreateBillingPeriod {
    pub user_id: Uuid,
    pub period_start: NaiveDate,
    pub period_end: NaiveDate,
    pub total_requests: i32,
    pub total_cost_cents: i32,
    pub is_current: bool,
    pub payment_status: PaymentStatus,
}

impl BillingPeriod {
    pub fn calculate_total_cost(total_requests: i32, cost_per_request: i32) -> i32 {
        total_requests * cost_per_request
    }
}
```

#### src/infrastructure/database/models/request_logs.rs
```rust
//! Request log model

use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use chrono::{DateTime, Utc};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "request_logs_status_type")]
pub enum RequestStatus {
    #[serde(rename = "SUCCESS")]
    #[sqlx(rename = "SUCCESS")]
    Success,
    #[serde(rename = "ERROR")]
    #[sqlx(rename = "ERROR")]
    Error,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct RequestLog {
    pub id: Uuid,
    pub user_id: Uuid,
    pub token_id: Option<Uuid>,
    pub billing_period_id: Option<Uuid>,
    pub service: String,
    pub request_ts: DateTime<Utc>,
    pub duration_ms: i32,
    pub request_bytes: i32,
    pub response_bytes: i32,
    pub status: RequestStatus,
    pub error_code: Option<String>,
    pub request_id: Uuid,
    pub flow_id: Option<String>,
    pub result: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CreateRequestLog {
    pub user_id: Uuid,
    pub token_id: Option<Uuid>,
    pub billing_period_id: Option<Uuid>,
    pub service: String,
    pub duration_ms: i32,
    pub request_bytes: i32,
    pub response_bytes: i32,
    pub status: RequestStatus,
    pub error_code: Option<String>,
    pub request_id: Uuid,
    pub flow_id: Option<String>,
    pub result: Option<String>,
}
```

#### src/infrastructure/database/models/invite_codes.rs
```rust
//! Invite code model

use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use chrono::{DateTime, Utc};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct InviteCode {
    pub id: Uuid,
    pub code: String,
    pub is_active: bool,
    pub expires_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
    pub used_at: Option<DateTime<Utc>>,
    pub used_by_user_id: Option<Uuid>,
    pub created_by_user_id: Option<Uuid>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CreateInviteCode {
    pub code: String,
    pub is_active: bool,
    pub expires_at: Option<DateTime<Utc>>,
    pub created_by_user_id: Option<Uuid>,
}

impl InviteCode {
    pub fn is_valid(&self) -> bool {
        let now = Utc::now();

        if !self.is_active {
            return false;
        }

        if let Some(expires_at) = self.expires_at {
            if expires_at <= now {
                return false;
            }
        }

        if self.used_at.is_some() {
            return false;
        }

        true
    }

    pub fn is_expired(&self) -> bool {
        if let Some(expires_at) = self.expires_at {
            expires_at <= Utc::now()
        } else {
            false
        }
    }

    pub fn is_used(&self) -> bool {
        self.used_at.is_some()
    }
}
```

#### src/infrastructure/database/models/settings.rs
```rust
//! Settings model

use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Settings {
    pub id: i64,
    pub cost_per_request_cents: i32,
    pub openai_model: Option<String>,
    pub openai_timeout_s: i32,
    pub app_domain: Option<String>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UpdateSettings {
    pub cost_per_request_cents: Option<i32>,
    pub openai_model: Option<String>,
    pub openai_timeout_s: Option<i32>,
    pub app_domain: Option<String>,
}
```

#### src/infrastructure/database/migrations.rs
```rust
//! Database migration utilities

use sqlx::PgPool;
use crate::AppError;

/// Run all pending migrations
pub async fn run_migrations(pool: &PgPool) -> Result<(), AppError> {
    sqlx::migrate!("./migrations")
        .run(pool)
        .await
        .map_err(|e| {
            tracing::error!("Failed to run migrations: {:?}", e);
            AppError::Database(e)
        })?;

    tracing::info!("Database migrations completed successfully");
    Ok(())
}

/// Verify migration status
pub async fn verify_migrations(pool: &PgPool) -> Result<(), AppError> {
    let result = sqlx::query!(
        "SELECT version, description FROM _sqlx_migrations ORDER BY version"
    )
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Database(e))?;

    tracing::info!("Applied migrations:");
    for migration in result {
        tracing::info!("  {}: {}", migration.version, migration.description);
    }

    Ok(())
}
```

### Step 4: Update Configuration

#### Update src/config/settings.rs
```rust
// Add this to DatabaseSettings struct:
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseSettings {
    pub url: String,
    pub max_connections: u32,
    pub min_connections: u32,
    pub acquire_timeout_seconds: u64,
    pub idle_timeout_seconds: u64,
    pub max_lifetime_seconds: u64,
}
```

### Step 5: Update Cargo.toml for SQLx CLI
```toml
# Add to dev-dependencies in Cargo.toml
[dev-dependencies]
sqlx-cli = { version = "0.8", features = ["postgres"] }
tokio-test = "0.4"
tempfile = "3.0"
```

## Verification Steps

1. **Migration Syntax Check**:
   ```bash
   cd backend-rs
   sqlx migrate info --database-url "postgresql://trc_user:trc_password@localhost:5432/trc_platform"
   ```

2. **Run Migrations**:
   ```bash
   sqlx migrate run --database-url "postgresql://trc_user:trc_password@localhost:5432/trc_platform"
   ```

3. **Verify Schema**:
   ```bash
   psql postgresql://trc_user:trc_password@localhost:5432/trc_platform
   \dt
   \dT
   \di
   ```

4. **Test Database Connectivity**:
   ```bash
   cargo test database_health_check
   ```

5. **Check Model Compilation**:
   ```bash
   cargo check
   # Should compile without SQLx query errors
   ```

## Expected Files Created/Modified

### New Files:
- `migrations/V1__Create_initial_schema.sql`
- `migrations/V2__Add_performance_indexes.sql`
- `migrations/V3__Add_audit_triggers.sql`
- `src/infrastructure/database/mod.rs`
- `src/infrastructure/database/connection.rs`
- `src/infrastructure/database/models/mod.rs`
- `src/infrastructure/database/models/users.rs`
- `src/infrastructure/database/models/api_tokens.rs`
- `src/infrastructure/database/models/billing_periods.rs`
- `src/infrastructure/database/models/request_logs.rs`
- `src/infrastructure/database/models/invite_codes.rs`
- `src/infrastructure/database/models/settings.rs`
- `src/infrastructure/database/migrations.rs`

### Modified Files:
- `Cargo.toml` (added sqlx-cli to dev-dependencies)
- `src/config/settings.rs` (enhanced DatabaseSettings)

## Database Schema Verification

After running migrations, verify the schema matches Java version:

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('users', 'api_tokens', 'billing_periods', 'request_logs', 'invite_codes', 'settings');

-- Check enums exist
SELECT typname FROM pg_type WHERE typname IN ('payment_status_type', 'request_logs_status_type');

-- Check indexes exist
SELECT indexname FROM pg_indexes WHERE schemaname = 'public';
```

## Next Task Dependency

This task enables:
- **Task 3**: Configuration (requires database connection setup)
- **Task 4**: Domain Models (requires database models)
- **Task 5**: Repositories (requires database foundation)

## Troubleshooting

- **Migration Failures**: Check PostgreSQL version compatibility (16+ recommended)
- **SQLx Query Errors**: Ensure database connection is available during compilation
- **Permission Errors**: Verify database user has CREATE, ALTER, INDEX permissions
- **Connection Issues**: Check DATABASE_URL format and network connectivity

## Success Metrics

- [ ] All migration files created with correct SQL syntax
- [ ] Migrations run successfully without errors
- [ ] Database schema matches Java backend exactly
- [ ] All model structs compile with SQLx derive macros
- [ ] Database health check passes
- [ ] Connection pool creates successfully
- [ ] Project compiles without SQLx-related errors

---

**This task establishes the foundation for all data persistence operations using SQLx's compile-time guarantees.**
