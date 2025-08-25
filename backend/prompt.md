# Backend Codegen Prompt (Django + DRF)

> Use this prompt verbatim in your code‑gen tool. It must generate a working repo that runs with `docker compose -f compose.yml up` and passes tests on first run.

---

You are an expert Django/DRF engineer. Create a production‑ready **MVP backend** for the **Image Solve Platform** with three Django apps: `customers`, `usage`, and `core`. Keep it simple and shippable.

## Tech & Repo

* **Python 3.12**, **Django 5.x**, **Django REST Framework**, **psycopg2-binary**, **argon2-cffi**, **drf-spectacular**, **django-cors-headers**.
* **UV**: Use uv for initialization and project and dependency management.
* **Typing & QA**: **mypy** (strict), **django-stubs**, **djangorestframework-stubs**, **ruff**, **black**, **pytest**, **pytest-django**, **model-bakery**, **requests-mock**.
* Runtime: **PostgreSQL**, Docker, **compose.yml**, gunicorn. Optional: **redis** for rate limiting (feature‑flagged; off by default).

Create repository root with **top‑level modules (no `src/`)**:

```
backend/
  Dockerfile
  compose.yml
  Makefile
  README.md
  manage.py
  pyproject.toml
  mypy.ini
  .gitignore
  .envrc # for direnv
  .env # for direnv
  config/          # settings, urls, wsgi, asgi
  customers/
  usage/
  core/
```

## Environment & Settings

* Read configuration from **environment variables only**. **Do not use python‑dotenv.**
* Provide `.envrc` (for **direnv**) exporting variables; document `direnv allow` in README. Example:

```sh
dotenv
```

* Provide `.env` (for **direnv**) exporting variables; document `direnv allow` in README. Example:

  ```sh
  DJANGO_SECRET_KEY="change-me"
  DJANGO_DEBUG=0
  DATABASE_URL="postgres://postgres:postgres@localhost:5432/app"
  ALLOWED_HOSTS="*"
  DEFAULT_FROM_EMAIL="no-reply@example.com"
  EMAIL_HOST="localhost"
  EMAIL_PORT=1025
  EMAIL_HOST_USER=""
  EMAIL_HOST_PASSWORD=""
  EMAIL_USE_TLS=false
  OPENAI_API_KEY=""
  OPENAI_MODEL="gpt-vision"
  OPENAI_TIMEOUT_S=30
  COST_PER_REQUEST_CENTS=100
  CORS_ALLOWED_ORIGINS="http://localhost:5173"
  ```
* Use `argon2` as password hasher. `TIME_ZONE=UTC`, `USE_TZ=True`.
* Installed apps: `corsheaders`, `drf_spectacular`, `rest_framework`, `customers`, `usage`, `core`.
* DRF defaults: JSON only, pagination (page size 25), exception handler returning RFC7807 (problem+json). Auth classes: session + custom bearer token.
* Spectacular: `/api/schema/` and `/api/docs/` (Swagger UI).

## Typing & Tooling

* **mypy**: enable strict settings. Include `mypy.ini`:

  ```ini
  [mypy]
  python_version = 3.12
  warn_unused_configs = True
  disallow_any_generics = True
  disallow_subclassing_any = True
  disallow_untyped_calls = True
  disallow_untyped_defs = True
  disallow_incomplete_defs = True
  check_untyped_defs = True
  no_implicit_optional = True
  warn_redundant_casts = True
  warn_unused_ignores = True
  warn_return_any = True
  strict_equality = True
  plugins = mypy_django_plugin.main

  [mypy.plugins.django-stubs]
  django_settings_module = config.settings
  ```
* All Python code must be fully typed. Add CI step `make typecheck`.

## Database Models

### customers

* `User` (custom email user)

  * fields: `id (UUID)`, `email (unique)`, `password`, `is_active`, `is_staff`, `email_verified_at (datetime|null)`
* `InviteCode`

  * **One‑time use tied to a user.** Fields: `code (unique str)`, `is_active (bool)`, `expires_at (datetime|null)`, `created_at`, `used_at (datetime|null)`, `used_by (FK→User|null, unique)`
  * Business rule: a code can be used **at most once**; when `used_by` is set, mark `is_active=false` and prevent reuse.
* `ApiToken`

  * `id (UUID)`, `user (FK)`, `name (str)`, `token_prefix (char[8])`, `token_hash (str)`, `created_at`, `revoked_at (datetime|null)`, `last_used_at (datetime|null)`

### usage

* `BillingPeriod`

  * `id (UUID)`, `user (FK)`, `period_start (date)`, `period_end (date)`, `total_requests (int)`, `total_cost_cents (int)`, `is_current (bool)`
  * **Payment tracking**: `payment_status (pending|paid|overdue|waived)`, `paid_at (datetime|null)`, `paid_amount_cents (int|null)`, `payment_reference (str|null)`, `payment_notes (text|null)`
  * Unique constraint on `(user, period_start)`. Indexes on payment status and dates.
  * Methods: `mark_as_paid()`, `mark_as_overdue()`, `mark_as_waived()`

* `RequestLog`

  * `id (UUID)`, `user (FK)`, `token (FK→ApiToken|null)`, `billing_period (FK→BillingPeriod|null)`, `service (str)`, `request_ts (auto_now_add)`, `duration_ms (int)`, `request_bytes (int)`, `response_bytes (int)`, `status (success|error)`, `error_code (str|null)`, `request_id (uuid, index)`

### core

* `Settings` (singleton id=1): `cost_per_request_cents (int)`, `openai_model (str)`, `openai_timeout_s (int)`

Register admin for all models (read‑only for logs). Index `User.email`, `InviteCode.code`, `RequestLog.request_ts`.

## Auth

* **Session auth** for customer portal endpoints.
* **Bearer token** for `/api/core/solve`:

  * Token creation: generate 32 random bytes → base64url string. Store **hash** (argon2) and 8‑char `token_prefix`. Return plain token **once** on create.
  * Middleware `TokenAuthMiddleware` extracts `Authorization: Bearer <token>`, finds token by prefix, verifies argon2 hash, checks not revoked and user active; attaches `request.user` and `request.token`.

## Email Verification & One‑time Invites

* Registration requires a valid **invite code**: active, not expired, **not used**.
* On successful signup, send email with a **signed verification link** (`/api/customers/verify-email?token=...`) valid 24h. After click, set `email_verified_at`.
* Disallow login until email verified.
* When verification completes, **mark invite code as used**: set `used_at=now`, `used_by=<user>`, and `is_active=false`.

## API Endpoints (paths & behavior)

Mount all under `/api`.

### customers (public/session)

* `POST /api/customers/register` `{email, password, invite_code}` → 202 Accepted (verification required). Errors: `invalid_invite`, `invite_used`, `email_exists`.
* `POST /api/customers/login` → session cookie.
* `POST /api/customers/logout` → 204.
* `GET /api/customers/verify-email?token=...` → 204.
* `POST /api/customers/password/change` (auth) `{old_password,new_password}` → 204.

**API Tokens** (auth)

* `GET /api/customers/tokens` → list.
* `POST /api/customers/tokens` `{name}` → 201 `{id, name, token_once, token_prefix, created_at}`.
* `DELETE /api/customers/tokens/{id}` → 204 (sets `revoked_at`).

**Usage (self)**

* `GET /api/customers/usage/requests?from=&to=&page=` → list of `RequestLog` with sizes only (no payloads).
* `GET /api/customers/usage/summary` → `{total_requests, total_cost_cents, by_period:[{title, count, cost_cents}]}` where server computes titles: Today, Yesterday, Last 7 Days, This Month.

**Billing (auth)**

* `GET /api/customers/billing/current` → current billing period summary.
* `GET /api/customers/billing/periods?status=` → list all billing periods with optional status filter.
* `GET /api/customers/billing/periods/{id}` → detailed requests for a specific billing period.

### core (bearer token)

* `POST /api/core/solve` accepts either `multipart/form-data` with `file` or `application/octet-stream` body. Returns `{request_id, result, model, duration_ms}`.

  * On each call: start timer, validate token, call OpenAI Vision (stub client `openai_client.solve_image(bytes, model, timeout)`), get/create current billing period, record `RequestLog` with billing period reference, update billing period totals (requests + cost), and respond.
  * Do **not** persist image bytes or OpenAI response body (MVP). Only sizes + metadata.

## Serializers & Views

* Use DRF ViewSets where natural; otherwise APIView + explicit routes.
* Enforce permissions: `IsAuthenticated` (session) or custom `IsTokenAuthenticated` (core).
* Validation messages are short and machine‑readable; include error `code` fields.

## Middleware & Utilities

* `TokenAuthMiddleware` (as above).
* `request_id` generator (uuid4) per request; add to response header `X-Request-ID` and to logs.
* Problem+JSON exception handler.
* `get_or_create_current_billing_period(user)` helper in `usage/utils.py` to manage monthly billing periods.

## OpenAI Client Stub

* Thin wrapper `core/services/openai_client.py` that reads env vars and sends the image to OpenAI Vision using `requests`. Unit tests mock HTTP.
* Handle timeouts, HTTP errors; map to `openai_error` codes.

## URLs & Routing

* Root `/healthz` returns DB connectivity and (mock) OpenAI client ping.
* `/api/schema/` + `/api/docs/` from `drf-spectacular`.

## CORS & CSRF

* Enable CSRF for session routes; exempt only the bearer‑token core endpoint if needed.
* CORS allowlist from `CORS_ALLOWED_ORIGINS`.

## Docker & Compose

* `Dockerfile` (multi‑stage): build deps → run with gunicorn.
* **`compose.yml`** services: `web`, `db` (postgres), optional `redis`. Healthchecks for `web` and `db`.

## Makefile Targets

* `make dev` → runserver (assumes direnv exports are active)
* `make test` → pytest
* `make migrate` → migrations
* `make superuser`
* `make typecheck` → mypy
* `make lint` → ruff
* `make format` → black

## Tests (must pass)

* Tokens (hash/verify), invites (**one‑time use tied to user**), email verification.
* Auth (cannot login before verify).
* Core solve happy path + timeout/error mapping.
* Usage summary periods and cost math.
* Billing period creation and payment status changes.
* Request logs properly linked to billing periods.

## Seed & Admin

* Management command `bootstrap_demo` to create: one admin, one **unused** invite code, one verified user, one token, one Settings row.
* Management command `create_billing_periods` to initialize billing periods for all active users.
* Management command `mark_overdue_periods` to mark unpaid periods as overdue (for cron jobs).
* Admin interface for `BillingPeriod` with actions to mark as paid/overdue/waived.

## Output & Acceptance

* On repo generation, print:

  1. `docker compose -f compose.yml up --build`
  2. `make migrate && python manage.py bootstrap_demo`
  3. Open `http://localhost:8000/api/docs/`.
* All endpoints must be reachable; `/api/schema/` must render.
* `POST /api/core/solve` must accept an image and return a mocked result when `OPENAI_API_KEY` unset (fallback stub mode).

---

### Example Schemas

**Token create response**

```json
{ "id":"uuid", "name":"CLI", "token_prefix":"tok_ab12cd34", "token_once":"tok_ab12cd34....", "created_at":"2025-08-11T12:00:00Z" }
```

**RequestLog item**

```json
{ "id":"uuid", "request_ts":"2025-08-11T12:34:56Z", "service":"core.image_solve", "status":"success", "duration_ms":412, "request_bytes":58213, "response_bytes":987, "request_id":"3a1e...", "token_prefix":"tok_ab12cd34" }
```

---

Deliver clean, fully‑typed, idiomatic code with comments only where non‑obvious. Keep dependencies minimal. Ship it so it runs first try.

