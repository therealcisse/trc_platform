# UI Implementation Guide for Backend API

## Pages to Implement

---

## 1. Authentication Pages

### 1.1 Registration Page (`/register`)
- **Endpoint:** `POST /api/customers/register`
- **Required Fields:**
  - Email
  - Password
  - Password confirmation
  - Invite code (required for registration)
- **Flow:**
  - Submit registration form with valid invite code
  - Show success message about verification email
  - Redirect to login page
- **Error Handling:**
  - Invalid invite code: Show error message "Invalid or expired invite code"
  - Missing invite code: Show validation error

### 1.2 Login Page (`/login`)
- **Endpoint:** `POST /api/customers/login`
- **Required Fields:**
  - Email
  - Password
- **Response:**
  - User ID and email on success
  - Session cookie is set automatically
- **Flow:**
  - After successful login, redirect to dashboard
  - Show error message for invalid credentials

### 1.3 Email Verification Page (`/verify-email`)
- **Endpoint:** `GET /api/customers/verify-email?token={token}`
- **Flow:**
  - Handle verification link from email
  - Show success/error message
  - Redirect to login or dashboard

### 1.4 Change Password Page (`/account/password`)
- **Endpoint:** `POST /api/customers/password/change`
- **Required Fields:**
  - Current password
  - New password
  - New password confirmation
- **Prerequisites:**
  - User must be authenticated
  - Email must be verified
- **Flow:**
  - Show success message
  - Optionally logout and redirect to login

### 1.5 Logout
- **Endpoint:** `POST /api/customers/logout`
- **Flow:**
  - Call logout endpoint
  - Clear local state
  - Redirect to login page

---

## 2. API Token Management Pages

### 2.1 Token List Page (`/tokens`)
- **Endpoint:** `GET /api/customers/tokens`
- **Display:**
  - List of active and revoked tokens
  - Token name
  - Token prefix (for identification)
  - Creation date
  - Last used date
  - Revocation status
- **Actions:**
  - Create new token button
  - Revoke token action for each active token

### 2.2 Create Token Modal/Page
- **Endpoint:** `POST /api/customers/tokens`
- **Required Fields:**
  - Token name (descriptive name)
- **Response:**
  - Full token (only shown once)
  - Token ID
  - Token prefix
- **Flow:**
  - Show the full token with copy button
  - Warning that token won't be shown again
  - Add to token list

### 2.3 Revoke Token Action
- **Endpoint:** `DELETE /api/customers/tokens/{token_id}`
- **Flow:**
  - Confirmation dialog
  - Update token status in list
  - Show success message

---

## 3. Usage and Billing Pages

### 3.1 Dashboard/Overview Page (`/dashboard`)
- **Endpoints:**
  - `GET /api/customers/billing/current` - Current billing period
  - `GET /api/customers/usage/summary` - Usage summary
- **Display:**
  - Current billing period info (label, dates, status)
  - Total requests in current period
  - Total cost in current period
  - Quick usage stats (Today, Yesterday, Last 7 days, This month)
  - Last request timestamp

### 3.2 Billing Periods List Page (`/billing`)
- **Endpoint:** `GET /api/customers/billing/periods`
- **Query Parameters:**
  - `status` (optional) - Filter by payment status
- **Display:**
  - List of all billing periods
  - Period label (e.g., "2025-01")
  - Date range
  - Total requests
  - Total cost
  - Payment status (pending/paid/overdue)
  - Payment date and reference (if paid)
- **Actions:**
  - View details for each period
  - Filter by status

### 3.3 Billing Period Details Page (`/billing/{period_id}`)
- **Endpoint:** `GET /api/customers/billing/periods/{period_id}`
- **Query Parameters:**
  - `page` - For pagination
- **Display:**
  - Period summary (dates, total requests, total cost, status)
  - Paginated list of requests in that period
  - For each request:
    - Timestamp
    - Service used
    - Status
    - Duration (ms)
    - Request/Response size
    - Request ID

### 3.4 Usage History Page (`/usage`)
- **Endpoint:** `GET /api/customers/usage/requests`
- **Query Parameters:**
  - `from` - Start date filter
  - `to` - End date filter
  - `page` - Pagination
- **Display:**
  - Filterable list of all API requests
  - Date range picker
  - For each request:
    - Timestamp
    - Service
    - Status
    - Duration
    - Bytes transferred
    - Token used (prefix)
    - Request ID
- **Features:**
  - Pagination (25 items per page)
  - Export capability (implement client-side)

---

## 4. Navigation Structure

```
Main Navigation:
- Dashboard (default after login)
- API Tokens
- Billing
  - Current Period
  - History
  - Usage Details
- Account
  - Change Password
  - Logout
```

---

## 5. Authentication Flow

```
1. Unauthenticated users:
   - Can access: Register, Login, Email Verification
   - Redirected to login for protected pages

2. Authenticated but unverified email:
   - Can access: Dashboard (limited), Logout
   - Show banner to verify email
   - Cannot create tokens or view detailed usage

3. Authenticated and verified:
   - Full access to all features
```

---

## 6. Error Handling

All endpoints return consistent error responses:
```json
{
  "detail": "Error message",
  "code": "error_code"
}
```

Handle these errors in the UI:
- 401: Redirect to login
- 403: Show permission denied message
- 404: Show not found message
- 400: Display validation errors
- 500: Show generic error message

---

## 7. State Management Recommendations

Store in client state:
- User info (id, email, verification status)
- Current billing period summary
- Active tokens list
- Recent usage statistics

Refresh periodically:
- Current billing period (every 5 minutes if on dashboard)
- Usage statistics (on page focus)

---

## 8. UI Components to Build

### Reusable Components:
- Authentication forms
- Token display card
- Usage chart/graph
- Billing period card
- Request log table
- Pagination controls
- Date range picker
- Status badges (paid/pending/overdue)

### Layouts:
- Public layout (for auth pages)
- Protected layout (with navigation)
- Dashboard widgets layout

---

## 9. API Base Configuration

- **Base URL:** Configure based on environment
  - Development: `http://localhost:8000/api`
  - Production: Configure based on deployment
- **Authentication:** Session-based (cookies)
- **Content-Type:** `application/json`
- **CSRF:** May require CSRF token for POST/PUT/DELETE requests

---

## 10. Additional Considerations

### Security:
- Always use HTTPS in production
- Store tokens securely (never in localStorage for sensitive tokens)
- Implement proper session timeout handling
- Clear sensitive data on logout

### Performance:
- Implement request caching where appropriate
- Use pagination for large datasets
- Consider implementing infinite scroll for request logs
- Lazy load billing period details

### User Experience:
- Show loading states for all async operations
- Implement proper error boundaries
- Add confirmation dialogs for destructive actions
- Provide clear feedback for all user actions
- Consider adding tooltips for complex features

This structure provides a complete UI implementation roadmap that's framework-agnostic and focuses on the functional requirements and API integration points.
