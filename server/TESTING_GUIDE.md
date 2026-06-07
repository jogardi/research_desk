# Bearer Token Migration Testing Guide

## Overview

This guide helps you test the dual authentication system (cookies + bearer tokens) to ensure the migration is working correctly.

## Prerequisites

1. **Server Running**: Make sure your Flask server is running
2. **Test User**: Create a test user account or use existing credentials
3. **Python Requests**: Install `requests` library: `pip install requests`

## Quick Test

Run the comprehensive test script:

```bash
# Test against localhost:5000 (default)
python test_bearer_token_migration.py

# Test against custom URL
python test_bearer_token_migration.py http://your-server:port
```

## Manual Testing Steps

### 1. Test Cookie-Based Login (Existing Behavior)

```bash
curl -X POST http://localhost:5000/api/user/login \
  -H "Content-Type: application/json" \
  -d '{"login": "your-email@example.com", "password": "your-password"}' \
  -c cookies.txt -v
```

**Expected Response:**
```json
{
  "access_token": "your-token-here",
  "token_type": "Bearer", 
  "expires_in": 3600,
  "user": {
    "user_id": "user-id",
    "email": "your-email@example.com",
    "name": "Your Name",
    ...
  }
}
```

**Expected Cookies:** `user_token`, `user_id`, `user_email` should be set

### 2. Test Cookie-Based API Access

```bash
curl -X GET http://localhost:5000/api/user/info \
  -b cookies.txt -v
```

**Expected:** Should return user information successfully

### 3. Test Bearer Token API Access  

Extract the `access_token` from login response, then:

```bash
curl -X GET http://localhost:5000/api/user/info \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -v
```

**Expected:** Should return the same user information as cookie-based request

### 4. Test Mixed Authentication

Both methods should work for the same user session:

```bash
# These should both work and return the same data
curl -X GET http://localhost:5000/api/sessions/list -b cookies.txt
curl -X GET http://localhost:5000/api/sessions/list -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Test Logout

```bash
# Cookie-based logout
curl -X GET http://localhost:5000/api/user/logout -b cookies.txt

# Bearer token logout  
curl -X GET http://localhost:5000/api/user/logout -H "Authorization: Bearer YOUR_TOKEN"
```

## What Should Work

✅ **Existing Cookie-Based Clients**: Continue working without changes
✅ **New Bearer Token Clients**: Can authenticate using Authorization header
✅ **Login Endpoint**: Returns both cookie and bearer token format
✅ **All Protected Endpoints**: Accept both authentication methods
✅ **Session Sliding**: Works for both authentication methods
✅ **Logout**: Works for both authentication methods

## Common Issues & Troubleshooting

### Bearer Token Not Working

1. **Check Header Format**: Must be exactly `Authorization: Bearer TOKEN`
2. **Check Token**: Use the `access_token` from login response
3. **Check Server Logs**: Look for authentication errors
4. **Verify SessionManager**: Ensure `get_user_token_from_request()` handles Authorization header

### Cookies Not Working

1. **Check Domain/Path**: Cookies must match server domain
2. **Check Secure Flag**: HTTPS might be required in production
3. **Check SameSite**: May need adjustment for cross-origin requests

### Session Validation Issues

1. **Check before_request Hook**: Ensure it's running for protected endpoints
2. **Check Session Cache**: Verify Redis/memory cache is working
3. **Check Session Expiration**: Tokens might be expired

## Advanced Testing

### Test Session Sliding

Make requests with both auth methods and verify cookies are updated:

```bash
# Initial login
curl -X POST http://localhost:5000/api/user/login \
  -H "Content-Type: application/json" \
  -d '{"login": "test@example.com", "password": "password"}' \
  -c cookies.txt -v

# Wait a few seconds, then make request
sleep 5
curl -X GET http://localhost:5000/api/user/info -b cookies.txt -v

# Check if cookie expiration times were updated
```

### Test Rate Limiting

Verify rate limiting works with both auth methods:

```bash
# Should use user_id for rate limiting instead of IP
for i in {1..10}; do
  curl -X GET http://localhost:5000/api/user/info -H "Authorization: Bearer YOUR_TOKEN"
done
```

### Test Concurrent Sessions

Verify the same user can have both cookie and bearer token sessions:

```bash
# Terminal 1: Use cookies
curl -X GET http://localhost:5000/api/user/info -b cookies.txt

# Terminal 2: Use bearer token (same user)  
curl -X GET http://localhost:5000/api/user/info -H "Authorization: Bearer YOUR_TOKEN"
```

## Success Criteria

- [ ] Login returns bearer token format AND sets cookies
- [ ] All protected endpoints accept Authorization header
- [ ] All protected endpoints still accept cookies  
- [ ] Same user can authenticate with both methods simultaneously
- [ ] Session sliding works for both methods
- [ ] Logout works for both methods
- [ ] Rate limiting uses user_id from either auth method
- [ ] No breaking changes to existing cookie-based clients

## Next Steps After Testing

Once testing passes:

1. **Update Client Applications**: Gradually migrate to bearer tokens
2. **Custom Token Generation**: Replace Backendless tokens with custom tokens
3. **Remove Cookie Support**: After all clients migrated (optional)
4. **Add Token Refresh**: Implement refresh token logic
5. **Enhanced Security**: Add token scopes, expiration policies, etc. 