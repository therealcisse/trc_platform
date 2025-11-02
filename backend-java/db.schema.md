# TRC Platform Database Schema Documentation

## Overview & Architecture

The TRC Platform uses PostgreSQL as its primary database, designed with a **domain-driven architecture** that supports user authentication, API token management, usage tracking, and billing functionality.

### **Key Architectural Principles**

- **UUID Primary Keys**: All entities use UUID for distributed system compatibility
- **Optimistic Locking**: `version` columns implement concurrency control
- **Soft Deletion Pattern**: Timestamp fields track lifecycle events without data loss
- **Period-Based Billing**: Costs aggregated at monthly billing period level, not per-request
- **Comprehensive Audit Trail**: Every API request logged with timing and status
- **Multi-Factor Authentication**: Email verification combined with invite code system

### **Database Statistics**
- **7 Core Tables** (excluding Flyway migration history)
- **2 Custom Enum Types** for data integrity
- **28 Strategic Indexes** for query performance
- **Comprehensive Foreign Key Constraints** with cascade rules

---

## Custom Types (Enums)

### `payment_status_type`
Controls billing period payment state transitions.

| Value | Description | Business Meaning |
|-------|-------------|------------------|
| `pending` | New billing period awaiting payment | Default status for new periods |
| `paid` | Payment successfully processed | Period is financially settled |
| `overdue` | Payment past due date | Triggers collection workflows |
| `waived` | Payment voluntarily forgiven | Admin-approved waiver |

### `request_logs_status_type`
Tracks individual API request outcomes.

| Value | Description | Billing Impact |
|-------|-------------|----------------|
| `SUCCESS` | Request completed successfully | Increments billing counters |
| `ERROR` | Request failed or errored | No billing impact |

---

## User Management Domain

### `users`
Central user account table with authentication and profile management.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | NOT NULL | - | Primary key, UUID for distributed systems |
| `email` | `varchar(255)` | NOT NULL | - | Unique email address for login |
| `password_hash` | `varchar(255)` | NOT NULL | - | Argon2-hashed password for security |
| `is_active` | `boolean` | NOT NULL | `true` | Account status - soft delete support |
| `is_staff` | `boolean` | NOT NULL | `false` | Administrative access flag |
| `email_verified_at` | `timestamptz` | YES | - | Email verification timestamp |
| `date_joined` | `timestamptz` | NOT NULL | - | Account creation timestamp |
| `user_accepted_terms` | `boolean` | NOT NULL | `false` | Legal terms acceptance |
| `user_acknowledged_disclaimer` | `boolean` | NOT NULL | `false` | Disclaimer acknowledgment |
| `version` | `bigint` | YES | - | Optimistic locking version |

**Constraints:**
- `users_email_key`: UNIQUE on `email`
- `chk_email_not_blank`: CHECK `length(email) > 0`

**Indexes:**
- `users_pkey`: PRIMARY KEY on `id`
- `users_email_key`: UNIQUE on `email`
- `idx_users_email`: Query optimization for login
- `idx_users_active_email_verified`: Composite for active verified users
- `idx_users_is_active`: Soft delete queries
- `idx_users_is_staff`: Admin user queries
- `idx_users_staff_active`: Admin active user queries

### `invite_codes`
User invitation system with lifecycle management.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | NOT NULL | - | Primary key |
| `code` | `varchar(32)` | NOT NULL | - | Human-readable invite code |
| `is_active` | `boolean` | NOT NULL | `true` | Invitation availability status |
| `expires_at` | `timestamptz` | YES | - | Invitation expiration timestamp |
| `created_at` | `timestamptz` | NOT NULL | - | Creation timestamp |
| `used_at` | `timestamptz` | YES | - | When invitation was redeemed |
| `used_by_user_id` | `uuid` | YES | - | User who used this invitation |
| `created_by_user_id` | `uuid` | YES | - | Admin who created invitation |

**Constraints:**
- `invite_codes_code_key`: UNIQUE on `code`

**Foreign Keys:**
- `created_by_user_id` → `users.id` (no cascade - preserve audit trail)
- `used_by_user_id` → `users.id` (no cascade - preserve audit trail)

**Indexes:**
- `invite_codes_pkey`: PRIMARY KEY on `id`
- `invite_codes_code_key`: UNIQUE on `code`
- `idx_code`: Fast lookup for code redemption
- `idx_invite_created_by`: Admin tracking queries

---

## API Access Domain

### `api_tokens`
Programmatic access tokens with lifecycle management.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | NOT NULL | - | Primary key |
| `user_id` | `uuid` | NOT NULL | - | Token owner |
| `token_hash` | `varchar(255)` | NOT NULL | - | Secure hash for token verification |
| `token_prefix` | `varchar(64)` | NOT NULL | - | Human-readable prefix for identification |
| `name` | `varchar(255)` | NOT NULL | - | User-defined token name |
| `created_at` | `timestamptz` | NOT NULL | - | Token creation timestamp |
| `last_used_at` | `timestamptz` | YES | - | Last successful usage timestamp |
| `expires_at` | `timestamptz` | YES | - | Token expiration timestamp |
| `revoked_at` | `timestamptz` | YES | - | Token revocation timestamp |

**Constraints:**
- `api_tokens_token_hash_key`: UNIQUE on `token_hash`

**Foreign Keys:**
- `user_id` → `users.id` (CASCADE on delete)

**Indexes:**
- `api_tokens_pkey`: PRIMARY KEY on `id`
- `api_tokens_token_hash_key`: UNIQUE on `token_hash`
- `idx_api_tokens_token_hash`: Fast token verification

---

## Billing & Usage Domain

### `billing_periods`
Monthly billing cycles with aggregated cost tracking.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | NOT NULL | - | Primary key |
| `user_id` | `uuid` | NOT NULL | - | Billing period owner |
| `period_start` | `date` | NOT NULL | - | Monthly period start date |
| `period_end` | `date` | NOT NULL | - | Monthly period end date |
| `total_requests` | `integer` | NOT NULL | `0` | Count of billable requests |
| `total_cost_cents` | `integer` | NOT NULL | `0` | Aggregated cost in cents |
| `is_current` | `boolean` | NOT NULL | `false` | Current billing period flag |
| `payment_status` | `payment_status_type` | NOT NULL | `'pending'` | Payment state |
| `paid_at` | `timestamptz` | YES | - | Payment timestamp |
| `paid_amount_cents` | `integer` | YES | - | Actual payment amount |
| `payment_reference` | `varchar(255)` | YES | - | External payment reference |
| `notes` | `text` | YES | - | Admin notes or adjustments |
| `version` | `bigint` | YES | - | Optimistic locking version |

**Foreign Keys:**
- `user_id` → `users.id` (CASCADE on delete)

**Indexes:**
- `billing_periods_pkey`: PRIMARY KEY on `id`
- `idx_current_period`: Fast lookup for current billing period
- `idx_user_period`: Composite for user billing history
- `idx_billing_payment_status`: Payment status queries

### `request_logs`
Comprehensive API request logging for usage tracking.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | NOT NULL | - | Primary key |
| `user_id` | `uuid` | NOT NULL | - | Request initiator |
| `token_id` | `uuid` | YES | - | API token used (if applicable) |
| `billing_period_id` | `uuid` | YES | - | Associated billing period |
| `service` | `varchar(255)` | NOT NULL | - | Service identifier (e.g., 'core.image_solve') |
| `request_ts` | `timestamptz` | NOT NULL | - | Request timestamp |
| `duration_ms` | `integer` | NOT NULL | - | Processing duration in milliseconds |
| `request_bytes` | `integer` | NOT NULL | - | Request payload size in bytes |
| `response_bytes` | `integer` | NOT NULL | - | Response payload size in bytes |
| `status` | `request_logs_status_type` | NOT NULL | - | Request outcome |
| `error_code` | `varchar(50)` | YES | - | Error code for failed requests |
| `request_id` | `uuid` | NOT NULL | - | Unique request identifier |
| `flow_id` | `varchar(255)` | YES | - | Request flow correlation ID |
| `result` | `text` | YES | - | Request result or error details |

**Foreign Keys:**
- `user_id` → `users.id` (CASCADE on delete)
- `token_id` → `api_tokens.id` (CASCADE on delete)
- `billing_period_id` → `billing_periods.id` (CASCADE on delete)

**Indexes:**
- `request_logs_pkey`: PRIMARY KEY on `id`
- `idx_request_id`: Fast request lookup by ID
- `idx_request_ts`: Time-based queries and analytics
- `idx_user_timestamp`: User activity history
- `idx_flow_id`: Request flow tracing

---

## System Configuration Domain

### `settings`
System-wide configuration parameters.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `bigint` | NOT NULL | - | Primary key (single row) |
| `cost_per_request_cents` | `integer` | NOT NULL | `100` | Cost per API request in cents |
| `openai_model` | `varchar(255)` | YES | - | OpenAI model identifier |
| `openai_timeout_s` | `integer` | NOT NULL | `30` | OpenAI API timeout in seconds |
| `app_domain` | `varchar(1024)` | YES | - | Application domain for links/emails |
| `updated_at` | `timestamptz` | NOT NULL | - | Last configuration update |

**Indexes:**
- `settings_pkey`: PRIMARY KEY on `id`

### `flyway_schema_history`
Database migration version tracking (Flyway-managed).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `installed_rank` | `integer` | NOT NULL | - | Migration installation order |
| `version` | `varchar(50)` | YES | - | Migration version |
| `description` | `varchar(200)` | NOT NULL | - | Migration description |
| `type` | `varchar(20)` | NOT NULL | - | Migration type |
| `script` | `varchar(1000)` | NOT NULL | - | Migration script name |
| `installed_on` | `timestamptz` | NOT NULL | - | Installation timestamp |
| `execution_time` | `integer` | NOT NULL | - | Migration execution time (ms) |
| `success` | `boolean` | NOT NULL | - | Migration success status |

**Indexes:**
- `flyway_schema_history_pk`: PRIMARY KEY on `installed_rank`
- `flyway_schema_history_s_idx`: Composite index on `success` and `version`

---

## Relationships & Foreign Keys

### **Primary Relationship Flow**
```
users (1) ───→ (N) api_tokens
   │              │
   │              └──→ (N) request_logs
   │
   ├──→ (N) billing_periods ───→ (N) request_logs
   │
   ├──→ (N) invite_codes (as created_by)
   │
   └──→ (N) invite_codes (as used_by)
```

### **Foreign Key Cascade Rules**
- **CASCADE DELETE**: User deletion removes all related tokens, billing periods, and request logs
- **CASCADE UPDATE**: UUID updates cascade (theoretical, UUIDs don't change)
- **Preserve Audit Trail**: Invite codes maintain creator/user relationships even if users deleted

### **Business Logic Relationships**
1. **Request → Billing**: Every successful request increments billing period counters
2. **Token Authentication**: API tokens optional - supports JWT and token-based auth
3. **Invite Lifecycle**: Created by admin → Used by new user → Invitation marked as used
4. **Period Management**: One current billing period per user, multiple historical periods

---

## Indexes & Performance Optimization

### **Primary Index Strategy**
| Index | Purpose | Query Pattern |
|-------|---------|---------------|
| `users_email_key` | User authentication | `WHERE email = ?` |
| `idx_api_tokens_token_hash` | API token verification | `WHERE token_hash = ?` |
| `idx_current_period` | Current billing lookup | `WHERE user_id = ? AND is_current = true` |
| `idx_request_ts` | Request analytics | `WHERE request_ts BETWEEN ? AND ?` |
| `idx_user_timestamp` | User activity history | `WHERE user_id = ? ORDER BY request_ts` |

### **Composite Indexes**
- `idx_users_active_email_verified`: `(is_active, email_verified_at)` - Active user filtering
- `idx_users_staff_active`: `(is_staff, is_active)` - Admin user queries
- `idx_user_period`: `(user_id, period_start)` - User billing history
- `idx_user_timestamp`: `(user_id, request_ts)` - User request chronology

### **Performance Considerations**
- **UUID Indexes**: All primary keys use UUID with appropriate btree indexes
- **Time-Series Queries**: Request logs optimized by timestamp and user_id
- **Authentication Fast Paths**: Email and token hash indexes for sub-100ms auth
- **Billing Analytics**: Composite indexes support monthly usage reporting

---

## Data Flow & Business Logic

### **API Request Lifecycle**
```
1. Authentication (JWT or API Token)
2. Request Processing
3. Request Logging (request_logs table)
4. Billing Period Update (if SUCCESS)
5. Response Return
```

### **Billing Calculation Formula**
```
total_cost_cents = total_requests × settings.cost_per_request_cents
```

### **User Registration Flow**
```
1. Admin creates invite_code
2. User receives invite and registers
3. Email verification required
4. Account activated (is_active = true, email_verified_at populated)
5. User can create API tokens and make requests
```

### **Cost Tracking Architecture**
- **Period-Level Aggregation**: Costs stored in billing_periods, not per-request
- **Real-Time Updates**: Billing period updated on every successful request
- **Audit Trail**: Request logs provide detailed usage history
- **Settings-Driven**: Cost per request configurable via settings table

---

## Security & Data Integrity

### **Authentication Security**
- **Password Hashing**: Argon2 algorithm with proper salt
- **Token Security**: Secure hashing, not storing actual tokens
- **Multi-Factor Auth**: Email + invite code required

### **Data Protection**
- **Soft Deletion**: `is_active` flag preserves user data
- **Optimistic Locking**: Version columns prevent concurrent modification conflicts
- **Foreign Key Integrity**: Cascading deletes maintain referential integrity
- **Audit Trail**: Comprehensive request logging with immutable records

### **Compliance Features**
- **Terms Tracking**: `user_accepted_terms` and disclaimer acknowledgment
- **Email Verification**: Required for account activation
- **Invite System**: Controlled user registration with admin oversight

---

*This schema documentation serves as a comprehensive reference for developers, database administrators, and AI assistants working with the TRC Platform database.*