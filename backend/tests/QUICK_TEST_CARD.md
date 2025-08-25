# 🚀 Quick Email Registration Test

## Prerequisites Started
✅ PostgreSQL: `localhost:5432`
✅ Mailcatcher SMTP: `localhost:1025`  
✅ Mailcatcher UI: `http://localhost:1080`
✅ Django Server: `http://localhost:8000`

## 📋 Test in 3 Steps

### 1️⃣ Register New User
```bash
curl -X POST http://localhost:8000/api/customers/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@test.com",
    "password": "Pass123!",
    "password_confirm": "Pass123!",
    "invite_code": "DEMO1234"
  }'
```
✅ Expect: HTTP 202

### 2️⃣ Check Email in Mailcatcher
Open browser: **http://localhost:1080**
- Click on "Verify your email address" email
- Copy the verification token from the URL

### 3️⃣ Verify & Login
```bash
# Verify email (use token from email)
curl "http://localhost:8000/api/customers/verify-email?token=YOUR_TOKEN_HERE"

# Login
curl -X POST http://localhost:8000/api/customers/login \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@test.com", "password": "Pass123!"}'
```

## 🎯 All-in-One Test Script
```bash
#!/bin/bash
EMAIL="test$(date +%s)@example.com"
PASS="TestPass123!"

echo "📧 Testing with email: $EMAIL"

# Register
echo -n "1. Registering... "
curl -s -X POST http://localhost:8000/api/customers/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"password_confirm\":\"$PASS\",\"invite_code\":\"DEMO1234\"}" \
  -o /dev/null -w "%{http_code}\n"

# Get verification token from Mailcatcher
echo -n "2. Getting verification link... "
sleep 1
TOKEN=$(curl -s http://localhost:1080/messages/1.plain | grep -oE 'token=.*' | cut -d'=' -f2)
echo "Got token"

# Verify
echo -n "3. Verifying email... "
curl -s "http://localhost:8000/api/customers/verify-email?token=$TOKEN" \
  -o /dev/null -w "%{http_code}\n"

# Login
echo -n "4. Logging in... "
curl -s -X POST http://localhost:8000/api/customers/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" | jq -r .email

echo "✅ Test complete!"
```

## 🔍 View Options
- **Mailcatcher UI**: http://localhost:1080
- **API Docs**: http://localhost:8000/api/docs/
- **Admin Panel**: http://localhost:8000/admin/
- **Database UI**: http://localhost:8090 (Adminer)

## 🛠 Troubleshooting Commands
```bash
# Check services
docker compose ps

# View Django logs
ps aux | grep runserver

# Test SMTP connection
telnet localhost 1025

# Clear Mailcatcher messages
curl -X DELETE http://localhost:1080/messages
```

## 📝 Notes
- Invite code `DEMO1234` can only be used once
- Tokens expire after 24 hours
- All emails go to Mailcatcher (no real sending)
- Emails are lost when Mailcatcher restarts
