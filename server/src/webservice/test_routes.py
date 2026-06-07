from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from shared.config import Config
from webservice.session_manager import protected, protected_session_data, protected_user_id, protected_user_email, protected_user_token

# Create a router for test endpoints
router = APIRouter()

# Public endpoints (no authentication required)
@router.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "FastAPI server is running"}

@router.get("/api/info")
async def app_info():
    return {
        "name": "Research Desk API",
        "version": "0.1.0",
        "framework": "FastAPI",
        "profile": Config.PROFILE
    }

# Protected endpoints using dependency injection
@router.get("/api/protected/simple")
async def protected_simple(_: None = Depends(protected)):
    """
    Example of a protected route that just needs authentication.
    Uses protected dependency.
    """
    return {"message": "This is a protected endpoint", "authenticated": True}

@router.get("/api/protected/session-data")
async def protected_with_session_data(session_data: dict = Depends(protected_session_data)):
    """
    Example of a protected route that needs session data.
    Uses protected_get_session_data dependency.
    """
    return {
        "message": "This endpoint has access to session data",
        "user_id": session_data.get('user_id'),
        "email": session_data.get('email'),
        "last_activity": session_data.get('last_activity')
    }

@router.get("/api/protected/user-info")
async def protected_user_info(
    user_id: str = Depends(protected_user_id),
    user_email: str = Depends(protected_user_email)
):
    """
    Example of a protected route that uses specific user dependencies.
    Uses protected_get_user_id and  protected_get_user_email dependencies.
    """
    return {
        "message": "This endpoint gets specific user data",
        "user_id": user_id,
        "email": user_email
    } 