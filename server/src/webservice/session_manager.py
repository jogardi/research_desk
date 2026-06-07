from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
import secrets
from webservice.cache.cache import Cache
from shared.logger import Logger
from shared.config import Config

# FastAPI security scheme for Bearer token
security = HTTPBearer()

class SessionManager:
    @staticmethod
    def create_session(user_data: dict) -> str:
        """
        Creates a session with a custom access token and stores it in the session cache.
        Args:
            user_data: dict - The user data to create a session for.
        Returns:
            str: The custom access token for client use
        """
        # Generate our own secure access token
        session_token = secrets.token_urlsafe(32)

        session_data = { **user_data, 'last_activity': datetime.utcnow().isoformat() }
        print(f"*** create_session - session_data: {session_data}")
        # Store session using our custom token as the key
        Cache.set('session:' + session_token, session_data, Config.SESSION_TIMEOUT)
        
        return session_token

    @staticmethod
    def delete_session(session_token) -> bool:
        """
        Deletes a session from the session cache.
        Args:
            session_token: str - The session token to delete
        Returns:
            bool: True if session was found and deleted, False otherwise
        """
        Cache.delete('session:' + session_token)

    @staticmethod
    def update_session_kb_name(session_token: str, kb_name: str) -> None:
        """
        Set session data in the session cache.
        Args:
            session_token: str - The session token to set
            kb_name: str - The kb_name to set
        """
        # Update last_activity to reset idle timeout
        session_data = Cache.get('session:' + session_token)
        session_data['kb_name'] = kb_name
        session_data['last_activity'] = datetime.utcnow().isoformat()
        # Set the current kb_name in the session cache (also reset the idle timeout and last_activity)
        Cache.set('session:' + session_token, session_data, Config.SESSION_TIMEOUT)

    @staticmethod
    def _validate_session(credentials: HTTPAuthorizationCredentials) -> dict:
        """
        Internal function to validate session and return session data.
        """
        session_token = credentials.credentials  # Bearer token
        
        if session_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session token is required"
            )
        
        # Check if session exists in cache
        session_data = Cache.get('session:' + session_token)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid"
            )

        # Check idle timeout (sliding window)
        last_activity = datetime.fromisoformat(session_data['last_activity'])
        idle_duration = datetime.utcnow() - last_activity
        
        if idle_duration > timedelta(seconds=Config.USER_IDLE_TIMEOUT):
            Cache.delete('session:' + session_token)  # Cleanup expired session
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired due to inactivity"
            )

        # Slide session expiration (update last activity)
        session_data['last_activity'] = datetime.utcnow().isoformat()
        Cache.set('session:' + session_token, session_data, Config.SESSION_TIMEOUT)  # Reset TTL

        return session_data
    
#
# Protected dependencies
#
def protected(credentials: HTTPAuthorizationCredentials = Depends(security)) -> None:
    """
    Validates user session but doesn't return session data.
    Use this for routes that just need authentication but don't use session data.
    """
    SessionManager._validate_session(credentials)
    return None

def protected_session_data(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Validates user session. If valid, returns session data.
    Use this dependency in routes that need session data.
    """
    Logger.info(f"*** Session token: {credentials.credentials}")
    return SessionManager._validate_session(credentials)

def protected_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    FastAPI dependency to get current user ID.
    """
    session_data = SessionManager._validate_session(credentials)
    return session_data['user_id']

def protected_user_email(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    FastAPI dependency to get current user email.
    """
    session_data = SessionManager._validate_session(credentials)
    return session_data['email']

def protected_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    FastAPI dependency to get current user's Backendless token.
    """
    session_data = SessionManager._validate_session(credentials)
    return session_data['backendless_token']

def protected_user_kb_name(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    FastAPI dependency to get current user's knowledgebase sort name.
    """
    session_data = SessionManager._validate_session(credentials)
    return session_data['kb_name']