#!/usr/bin/env bash
# Idempotently create or update a superuser in the database.
#
# Usage examples:
#   # Provide a precomputed hash directly (must be a Spring Security compatible Argon2id string like $argon2id$v=19$m=...)
#   ADMIN_EMAIL=admin@trc-platform.local ADMIN_PASSWORD_HASH={{ADMIN_PASSWORD_HASH}} \
#     PGHOST=localhost PGPORT=5432 PGDATABASE=trc_platform PGUSER=trc_user PGPASSWORD={{PGPASSWORD}} \
#     ./scripts/create-superuser.sh
#
#   # Or provide a plaintext password and this script will generate an Argon2id hash
#   ADMIN_EMAIL=admin@trc-platform.local ADMIN_PASSWORD=admin123 \
#     PGHOST=localhost PGPORT=5432 PGDATABASE=trc_platform PGUSER=trc_user PGPASSWORD={{PGPASSWORD}} \
#     ./scripts/create-superuser.sh
#
# Notes:
# - When generating a hash, this script uses Argon2id parameters matching
#   Spring's Argon2PasswordEncoder.defaultsForSpringSecurity_v5_8():
#     type=argon2id, iterations=3, memory=64 MiB, parallelism=1, saltLength=16, hashLength=32
# - Prefer providing ADMIN_PASSWORD_HASH for full control. If absent, set ADMIN_PASSWORD
#   (defaults to "password") and the script will compute the hash.
# - The operation is safe to re-run. It uses ON CONFLICT(email) DO UPDATE to upsert the user.

set -euo pipefail

# Database connection, can be provided via standard libpq envs or inferred from app defaults
PGHOST=${PGHOST:-localhost}
PGPORT=${PGPORT:-5432}
PGDATABASE=${PGDATABASE:-trc_platform}
PGUSER=${PGUSER:-${DATABASE_USERNAME:-trc_user}}
PGPASSWORD=${PGPASSWORD:-${DATABASE_PASSWORD:-trc_password}}

# Superuser details
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@trc-platform.local}
ADMIN_USER_ID=${ADMIN_USER_ID:-550e8400-e29b-41d4-a716-446655440000}

# If no precomputed hash is provided, compute Argon2id hash matching Spring defaults
if [[ -z ${ADMIN_PASSWORD_HASH:-} ]]; then
  ADMIN_PASSWORD=${ADMIN_PASSWORD:-password}

  # Ensure argon2 CLI is available
  if ! command -v argon2 >/dev/null 2>&1; then
    echo "ERROR: argon2 CLI is required to generate password hashes but was not found in PATH." >&2
    echo "       Either install it (e.g., brew install argon2) or provide ADMIN_PASSWORD_HASH explicitly." >&2
    exit 1
  fi

  # Generate a random salt and compute Argon2id hash
  # Spring defaults for v5.8: type=argon2id, t=3, m=64MiB (m=16 log2 KiB), p=1, hash length=32 bytes
  if command -v openssl >/dev/null 2>&1; then
    SALT=$(openssl rand -base64 16 | LC_ALL=C tr -dc 'A-Za-z0-9' | cut -c1-16)
  elif command -v uuidgen >/dev/null 2>&1; then
    SALT=$(uuidgen | tr -d '-' | cut -c1-16)
  elif command -v xxd >/dev/null 2>&1; then
    SALT=$(dd if=/dev/urandom bs=16 count=1 2>/dev/null | xxd -p -c 256 | cut -c1-16)
  else
    # Last-resort deterministic fallback
    SALT=$(date +%s%N | shasum -a 256 | awk '{print $1}' | cut -c1-16)
  fi
  ADMIN_PASSWORD_HASH=$(printf '%s' "$ADMIN_PASSWORD" | argon2 "$SALT" -id -t 3 -m 16 -p 1 -l 32 -e)
fi

# Check psql availability
if ! command -v psql >/dev/null 2>&1; then
  echo "ERROR: psql is required but not found in PATH" >&2
  exit 1
fi

export PGPASSWORD

# Execute with psql
psql "host=$PGHOST port=$PGPORT dbname=$PGDATABASE user=$PGUSER" \
  -v ON_ERROR_STOP=1 \
  -c "INSERT INTO users (
    id, email, password_hash, is_active, is_staff,
    email_verified_at, date_joined, user_accepted_terms, user_acknowledged_disclaimer, version
  ) VALUES (
    '$ADMIN_USER_ID'::uuid, '$ADMIN_EMAIL', '$ADMIN_PASSWORD_HASH', true, true,
    NOW(), NOW(), true, true, 1
  )
  ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    is_active = true,
    is_staff = true,
    email_verified_at = COALESCE(users.email_verified_at, NOW()),
    user_accepted_terms = true,
    user_acknowledged_disclaimer = true;"

echo "Superuser ensured: $ADMIN_EMAIL"
