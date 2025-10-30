-- Performance indexes for users table optimization
-- These indexes will improve performance for UPDATE queries and common lookup patterns

-- Primary index for UPDATE queries (most important - speeds up WHERE id = ? AND version = ?)
CREATE INDEX IF NOT EXISTS idx_users_id_version ON users (id, version);

-- Email lookup index (for login and user lookup operations)
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- Active status index (for filtering active users)
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users (is_active);

-- Email verification status index (for filtering verified users)
CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users (email_verified_at);

-- Staff status index (for admin/staff user lookups)
CREATE INDEX IF NOT EXISTS idx_users_is_staff ON users (is_staff);

-- Composite index for common user filtering patterns (active + verified users)
CREATE INDEX IF NOT EXISTS idx_users_active_email_verified ON users (is_active, email_verified_at);

-- Composite index for staff user lookups (staff + active)
CREATE INDEX IF NOT EXISTS idx_users_staff_active ON users (is_staff, is_active);
