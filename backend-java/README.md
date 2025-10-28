# TRC Platform Java Backend

Spring Boot 3.3, Java 21 implementation of TRC Platform backend.

## Quick start

```bash
docker compose up --build
```

## Admin API summary

Base path: `/api/v1/admin`

## Bootstrap superuser

Run after migrations to create or update the admin user:

```bash
chmod +x scripts/create-superuser.sh
PGHOST=localhost PGPORT=5432 PGDATABASE=trc_platform PGUSER=trc_user PGPASSWORD={{PGPASSWORD}} \
ADMIN_EMAIL=admin@trc-platform.local ADMIN_PASSWORD_HASH={{ADMIN_PASSWORD_HASH}} \
./scripts/create-superuser.sh
```

- Use a Spring Security compatible hash for ADMIN_PASSWORD_HASH, for example a {bcrypt} hash. Do not pass plaintext passwords.

## Create invite codes

Create an invite code using admin credentials via the API:

```bash
chmod +x scripts/create-invite-code.sh
APP_URL=http://localhost:8080 \
ADMIN_EMAIL=admin@trc-platform.local ADMIN_PASSWORD={{ADMIN_PASSWORD}} \
INVITE_CODE=TESTCODE123 EXPIRES_AT=2025-12-31T23:59:59 \
./scripts/create-invite-code.sh
```

- Do not pass plaintext passwords in commands copied to logs. Provide via environment.
- If the invite already exists the script exits successfully.

## Bootstrap superuser

Run after migrations to create or update the admin user:

```bash
chmod +x scripts/create-superuser.sh
PGHOST=localhost PGPORT=5432 PGDATABASE=trc_platform PGUSER=trc_user PGPASSWORD={{PGPASSWORD}} \
ADMIN_EMAIL=admin@trc-platform.local ADMIN_PASSWORD_HASH={{ADMIN_PASSWORD_HASH}} \
./scripts/create-superuser.sh
```

- Use a Spring Security compatible hash for ADMIN_PASSWORD_HASH, for example a {bcrypt} hash. Do not pass plaintext passwords.

### Invite codes
- `GET /invites?page=0&size=20` List invite codes, paginated.
- `POST /invites` Create a new invite code. Body: `{ "code": "optional", "expiresAt": "2025-12-31T23:59:59" }`.
- `POST /invites/{code}/activate` Activate an invite code.
- `POST /invites/{code}/deactivate` Deactivate an invite code.
- `DELETE /invites/expired` Delete expired active invite codes. Returns integer count.

### Billing periods
- `GET /billing/periods?userId=<uuid>&status=<PENDING|PAID|OVERDUE|WAIVED>&page=0&size=20` List periods with filters.
- `POST /billing/periods/{periodId}/mark-paid` Mark as paid. Body: `{ "paidAmountCents": 1234, "paymentReference": "INV-2025-001", "paymentNotes": "SEPA", "paidAt": "2025-10-24T12:00:00" }`.
- `POST /billing/periods/{periodId}/mark-overdue` Mark overdue. Optional raw string body for notes.
- `POST /billing/periods/{periodId}/mark-waived` Mark waived. Optional raw string body for notes.
- `POST /billing/periods/{periodId}/unset-paid` Reset to pending and clear payment fields.

All responses are wrapped in `ApiResponse`.
