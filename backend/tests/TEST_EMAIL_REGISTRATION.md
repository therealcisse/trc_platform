# 📧 Testing Email Registration with Mailcatcher

This guide shows you how to test the complete email registration flow using Mailcatcher to capture and view emails locally.

## 🚀 Quick Start

### 1. Start Docker Services

Start the database and mailcatcher services:

```bash
# Start services
docker compose up -d

# Verify services are running
docker compose ps
```

You should see:
- PostgreSQL on port 5432
- Adminer on port 8090 
- Mailcatcher on ports 1025 (SMTP) and 1080 (Web UI)

### 2. Configure Django to Use Mailcatcher

Create a `.env` file with email settings:

```bash
# Create .env file
cat > .env << 'EOF'
DATABASE_URL=postgres://postgres:postgres@localhost:5432/app
DJANGO_SECRET_KEY=your-secret-key-here
EMAIL_HOST=localhost
EMAIL_PORT=1025
EMAIL_USE_TLS=false
DEFAULT_FROM_EMAIL=no-reply@imagesolve.local
EOF
```

### 3. Run Migrations and Bootstrap Data

```bash
# Run migrations
uv run python manage.py migrate

# Create demo data (includes invite codes)
uv run python manage.py bootstrap_demo
```

This creates:
- Admin user: `admin@example.com` (password: `admin123`)  
- Verified user: `user@example.com` (password: `user123`)
- **Unused invite code: `DEMO1234`** (important for registration!)

### 4. Start Django Development Server

```bash
# Start the server
uv run python manage.py runserver
```

Server will be available at: http://localhost:8000

### 5. Open Mailcatcher Web UI

Open your browser and go to: **http://localhost:1080**

This is where you'll see all captured emails.

## 🧪 Test the Registration Process

### Method 1: Using cURL

```bash
# Register a new user with the invite code
curl -X POST http://localhost:8000/api/customers/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "invite_code": "DEMO1234"
  }'
```

Expected response: HTTP 202 Accepted (no body)

### Method 2: Using HTTPie (if installed)

```bash
http POST localhost:8000/api/customers/register \
  email=newuser@example.com \
  password=SecurePass123! \
  password_confirm=SecurePass123! \
  invite_code=DEMO1234
```

### Method 3: Using Python Script

Create a test script `test_registration.py`:

```python
import requests
import json

# Register new user
response = requests.post(
    'http://localhost:8000/api/customers/register',
    json={
        'email': 'testuser@example.com',
        'password': 'TestPass123!',
        'password_confirm': 'TestPass123!',
        'invite_code': 'DEMO1234'
    }
)

print(f"Status: {response.status_code}")
if response.status_code == 202:
    print("✅ Registration successful! Check Mailcatcher for the verification email.")
else:
    print(f"❌ Error: {response.text}")
```

Run it:
```bash
uv run python test_registration.py
```

## 📬 View the Verification Email

1. Go to **http://localhost:1080** (Mailcatcher UI)
2. You should see the verification email with:
   - **From:** no-reply@imagesolve.local (or your configured address)
   - **To:** newuser@example.com
   - **Subject:** Verify your email address

3. Click on the email to view its contents
4. You'll see the verification link like:
   ```
   http://localhost:8000/api/customers/verify-email?token=<long-token-string>
   ```

## ✅ Complete Email Verification

### Option 1: Click the Link
Copy the verification URL from Mailcatcher and open it in your browser.

### Option 2: Use cURL
```bash
# Copy the token from the email and use it here
TOKEN="<paste-token-from-email>"
curl "http://localhost:8000/api/customers/verify-email?token=$TOKEN"
```

Expected response: HTTP 204 No Content (verification successful)

## 🔐 Test Login After Verification

```bash
# Try to login with the verified account
curl -X POST http://localhost:8000/api/customers/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePass123!"
  }'
```

Expected response:
```json
{
  "id": "uuid-here",
  "email": "newuser@example.com"
}
```

## 🎯 Test Different Scenarios

### 1. Invalid Invite Code
```bash
curl -X POST http://localhost:8000/api/customers/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test2@example.com",
    "password": "Pass123!",
    "password_confirm": "Pass123!",
    "invite_code": "INVALID"
  }'
```
Expected: HTTP 400 - Invalid invite code

### 2. Already Used Invite Code
Try registering again with `DEMO1234` after it's been used once.
Expected: HTTP 400 - Invite code already used

### 3. Expired Token
Wait 24 hours or modify the token string.
Expected: HTTP 400 - Token expired

### 4. Login Without Email Verification
Try logging in before verifying email.
Expected: HTTP 400 - Email not verified

## 📊 Mailcatcher Features

In the Mailcatcher UI (http://localhost:1080), you can:

- **View all emails** sent by the application
- **Search** emails by sender, recipient, or subject
- **View HTML and Plain Text** versions (this app uses plain text)
- **Download** emails as .eml files
- **Clear all messages** with the "Clear" button
- **Inspect email headers** and raw source

## 🔧 Troubleshooting

### Mailcatcher not receiving emails?
```bash
# Check if mailcatcher is running
docker compose ps

# Check Django email settings
uv run python manage.py shell -c "from django.conf import settings; print(f'Host: {settings.EMAIL_HOST}, Port: {settings.EMAIL_PORT}')"
```

### Port 1025 already in use?
```bash
# Stop any existing SMTP service
sudo lsof -i :1025
# Then restart mailcatcher
docker compose restart mailcatcher
```

### Can't access Mailcatcher UI?
```bash
# Check if port 1080 is accessible
curl http://localhost:1080
# Or try: http://127.0.0.1:1080
```

## 🛑 Cleanup

When done testing:
```bash
# Stop all services
docker compose down

# Remove volumes (warning: deletes database)
docker compose down -v
```

## 📝 Additional Notes

- Mailcatcher captures ALL emails sent to port 1025
- Emails are stored in memory (lost on restart)
- No real emails are sent externally
- Perfect for development and testing
- The invite code can only be used once per registration

## 🎉 Success Indicators

You know the email system is working when:
1. ✅ Registration returns HTTP 202
2. ✅ Email appears in Mailcatcher within seconds
3. ✅ Verification link works (HTTP 204)
4. ✅ User can login after verification
5. ✅ User cannot login before verification
