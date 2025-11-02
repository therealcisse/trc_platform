#!/usr/bin/env bash
# Create an invite code via the admin API using admin email/password.
# Requires: curl, and either python3 or jq to parse JSON.
#
# Usage examples:
#   APP_URL=http://localhost:8080 \
#   ADMIN_EMAIL=admin@trc-platform.local ADMIN_PASSWORD={{ADMIN_PASSWORD}} \
#   INVITE_CODE=TESTCODE123 EXPIRES_AT=2025-12-31T23:59:59 \
#   ./scripts/create-invite-code.sh
#
# Notes:
# - Do not echo or log secrets. Provide ADMIN_PASSWORD via env var.
# - Idempotent behavior: if the code already exists and API returns 409, the script will exit 0.

set -euo pipefail

APP_URL=${APP_URL:-http://localhost:8080}
LOGIN_PATH=${LOGIN_PATH:-/api/customers/login}
INVITES_PATH=${INVITES_PATH:-/api/v1/admin/invites}

ADMIN_EMAIL=${ADMIN_EMAIL:-admin@trc-platform.local}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-password}
INVITE_CODE=${INVITE_CODE:-}
EXPIRES_AT=${EXPIRES_AT:-}

if [[ -z "$ADMIN_EMAIL" || -z "$ADMIN_PASSWORD" || -z "$INVITE_CODE" ]]; then
  echo "ERROR: ADMIN_EMAIL, ADMIN_PASSWORD, and INVITE_CODE are required" >&2
  exit 2
fi

# Login and capture response
login_resp=$(curl -sS -w "\n%{http_code}" -X POST "${APP_URL}${LOGIN_PATH}" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}")

login_status=$(printf "%s" "$login_resp" | tail -n1)
login_body=$(printf "%s" "$login_resp" | sed '$d')

if [[ "$login_status" != "200" ]]; then
  echo "ERROR: Login failed with status $login_status: $login_body" >&2
  exit 1
fi

# Extract token using python3 if available, else jq
extract_token_with_python() {
  python3 - "$@" <<'PY'
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('token',''))
except Exception:
    print('')
PY
}

extract_token_with_jq() {
  jq -r '.token // empty'
}

token=""
if command -v python3 >/dev/null 2>&1; then
  token=$(printf "%s" "$login_body" | extract_token_with_python)
elif command -v jq >/dev/null 2>&1; then
  token=$(printf "%s" "$login_body" | extract_token_with_jq)
else
  echo "ERROR: Need python3 or jq to parse JSON" >&2
  exit 1
fi

if [[ -z "$token" || "$token" == "null" ]]; then
  echo "ERROR: Could not extract JWT token from login response" >&2
  exit 1
fi

# Build JSON payload
if [[ -n "$EXPIRES_AT" ]]; then
  payload=$(printf '{"code":"%s","expiresAt":"%s"}' "$INVITE_CODE" "$EXPIRES_AT")
else
  payload=$(printf '{"code":"%s"}' "$INVITE_CODE")
fi

# Create invite code
create_resp=$(curl -sS -w "\n%{http_code}" -X POST "${APP_URL}${INVITES_PATH}" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${token}" \
  -d "$payload")

create_status=$(printf "%s" "$create_resp" | tail -n1)
create_body=$(printf "%s" "$create_resp" | sed '$d')

case "$create_status" in
  200|201)
    echo "Invite code created: $INVITE_CODE"
    ;;
  409)
    echo "Invite code already exists: $INVITE_CODE"
    ;;
  *)
    echo "ERROR: Failed to create invite code, status $create_status: $create_body" >&2
    exit 1
    ;;
endcase
