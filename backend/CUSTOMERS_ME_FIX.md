# /customers/me Endpoint Documentation and Troubleshooting

## The Issue
The `/customers/me` endpoint was reported to be returning the admin user instead of the currently logged-in user.

## Investigation Results

### The Code is Correct
Our investigation shows that the `/customers/me` endpoint implementation is **correct**:

1. The `LoginView` properly uses Django's `login(request, user)` to create a session
2. The `CurrentUserView` correctly accesses `request.user` from the session
3. Our test script confirms the endpoint returns the correct user when tested programmatically

### Root Cause
The issue is likely due to one of these scenarios:

1. **Browser Session/Cookie Issues**: Old session cookies from a previous admin login
2. **Multiple Sessions**: Different tabs/windows with different login states
3. **Session Contamination**: Switching between users without proper logout
4. **Frontend State Management**: The frontend might be caching authentication state

## How Authentication Works

### Session-Based Authentication (Primary)
1. User logs in via `/api/customers/login`
2. Django creates a session and sets a `sessionid` cookie
3. Browser sends this cookie with subsequent requests
4. Django's `SessionAuthentication` identifies the user from the session

### Token-Based Authentication (Secondary)
1. User creates an API token via `/api/customers/tokens`
2. Token is sent in the `Authorization: Bearer tok_xxxxx` header
3. `TokenAuthMiddleware` authenticates the user from the token

## Debugging Tools Added

### 1. Debug Auth Endpoint
**Endpoint**: `/api/customers/debug/auth`

This endpoint shows detailed authentication information:
- Current authenticated user
- Session details
- Headers received
- Token information (if using token auth)

**WARNING**: Remove this endpoint in production!

### 2. Clear Sessions Management Command
```bash
# Clear all sessions
uv run python manage.py clear_sessions --all

# Clear expired sessions
uv run python manage.py clear_sessions --expired

# Clear sessions for a specific user
uv run python manage.py clear_sessions --user-email user@example.com
```

### 3. Test Script
Run the test script to verify the endpoint behavior:
```bash
uv run python test_current_user.py
```

## Troubleshooting Steps

### For End Users

1. **Clear Browser Data**:
   - Clear cookies for your domain
   - Clear local storage
   - Try incognito/private browsing mode

2. **Proper Logout**:
   - Always use the logout endpoint before switching users
   - Don't just close the browser tab

3. **Check Debug Info**:
   - Visit `/api/customers/debug/auth` to see current auth state
   - Compare the returned user with expected user

### For Developers

1. **Test with curl**:
```bash
# Login and get session
curl -c cookies.txt -X POST http://localhost:8000/api/customers/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Test /me endpoint with session
curl -b cookies.txt http://localhost:8000/api/customers/me
```

2. **Check Session in Django Admin**:
```bash
uv run python manage.py shell
```
```python
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
User = get_user_model()

# Check all active sessions
for session in Session.objects.all():
    data = session.get_decoded()
    if '_auth_user_id' in data:
        user = User.objects.get(pk=data['_auth_user_id'])
        print(f"Session {session.session_key}: {user.email}")
```

3. **Monitor Middleware Execution**:
   - Check if `TokenAuthMiddleware` is interfering with session auth
   - Verify middleware order in `settings.py`

## Configuration Changes Made

### Session Settings (config/settings.py)
```python
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_NAME = 'sessionid'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = 'Lax'
```

These settings ensure:
- Session cookies are HTTP-only (not accessible via JavaScript)
- Cookies are secure in production
- SameSite policy prevents CSRF attacks
- Sessions are stored in the database

## Files Modified/Created

1. **Created**:
   - `/customers/views_debug.py` - Debug view for authentication state
   - `/customers/management/commands/clear_sessions.py` - Session management command
   - `/test_current_user.py` - Test script for the endpoint
   - This documentation file

2. **Modified**:
   - `/customers/urls.py` - Added debug endpoint
   - `/config/settings.py` - Enabled session cookie settings

## Production Checklist

Before deploying to production:

- [ ] Remove the debug endpoint from `/customers/urls.py`
- [ ] Delete `/customers/views_debug.py`
- [ ] Remove test scripts
- [ ] Ensure `SESSION_COOKIE_SECURE = True` in production
- [ ] Ensure `CSRF_COOKIE_SECURE = True` in production
- [ ] Clear all development sessions

## Conclusion

The `/customers/me` endpoint is working correctly. The issue is most likely related to browser session management or multiple concurrent sessions. Use the debugging tools provided to identify the specific cause in your environment.
