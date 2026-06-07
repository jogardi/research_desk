from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityMiddleware(BaseHTTPMiddleware):
    """Minimal middleware for security and cache control"""
    
    async def dispatch(self, request: Request, call_next):
        # Block access to .env files for security
        if '.env' in request.url.path:
            return JSONResponse(
                status_code=403,
                content={'error': 'Invalid access'}
            )

        # Process the request
        response = await call_next(request)
        
        # Disable caching for all responses (including OPTIONS/CORS preflight)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        # For OPTIONS requests (CORS preflight), add additional headers to prevent caching
        if request.method == 'OPTIONS':
            response.headers['Access-Control-Max-Age'] = '0'  # Don't cache preflight
        
        return response 