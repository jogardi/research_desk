from datetime import datetime, timedelta
import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from shared.config import Config
from shared.logger import Logger
from webservice.persistence.user_mgmt_backendless import UserMgmtBackendless 
from webservice.persistence.contact_sqlite import ContactSqlite
from webservice.notification.notification_service import NotificationService
from webservice.session_manager import SessionManager, protected_user_id, protected_user_kb_name, protected_user_token, protected_user_email
from webservice.persistence.research_desk_session_sqlite import ResearchDeskSessionSqlite
from webservice.schemas.user import (
    LoginRequest, UserResponse, LoginResponse, RegisterRequest, ProfileRequest,
    ContactRequest, ShareRequest, AllUsersResponse, ChangePasswordRequest
)
from webservice.schemas.common import MessageResponse

# FastAPI Router (for converted routes)
router = APIRouter(tags=["user"])

# Security scheme for FastAPI
security = HTTPBearer()

@router.post("/api/user/login", response_model=LoginResponse)
def login(credentials: LoginRequest):
    """
    Log in an existing user with the Backendless API.
    """
   
    # print(credentials)
    
    # login user with the backendless API:
    user_data, error, status_code = UserMgmtBackendless.login(credentials.dict())
    if error is not None:
        raise HTTPException(status_code=status_code, detail=error)
    
    app_user, error, status_code = UserMgmtBackendless.get_app_user(user_data['email'], user_data['user-token'])
    if error is not None:
        raise HTTPException(status_code=status_code, detail=error)
    if app_user is None:
        Logger.error("TRD user not found for org: " + Config.ORG_NAME + " and email: " + user_data['email'], report=True)
        raise HTTPException(status_code=404, detail="TRD user not found.")
    
    print('*** TRD user data:')
    # Example shape: {'kb_permission_list': 'demo', 'org': 'DEV', 'default_kb': 'demo', 'email': 'user@example.com'}
    
    # get the kb_list from the Config.knowledgebases for the user based on the kb_permission_list
    kb_permission_list = app_user.get('kb_permission_list', '').split(',')
    kb_list = [{"kb_name": kb.SHORT_NAME, "kb_display_name": kb.DISPLAY_NAME} 
               for kb in Config.knowledgebases if kb.SHORT_NAME in kb_permission_list]
    
    # resolve the kb_name for the user based on the kb_permission_list and the default_kb
    try:
        kb_name = ResearchDeskSessionSqlite.resolve_kb_name(user_data['objectId'], 
                        kb_list, app_user.get('default_kb', ''))
    except Exception as e:
        Logger.error("Failed to resolve kb_name", exception=e, report=True)
        raise HTTPException(status_code=404, detail="Failed to get sessions.")

    print(f"*** Login - kb_name: {kb_name}")  
    
    user = {
        'user_id': user_data['objectId'],
        'backendless_token': user_data['user-token'],  # Backendless token for internal use
        'email': user_data['email'],
        'name': user_data.get('name', ''),
        'account_type': user_data.get('accountType', ''),
        'opted_in': user_data.get('opted_in', False),
        'is_closed': user_data.get('is_closed', False),
        'kb_name': kb_name
    }
    
    # Create session and get our custom access token
    session_token = SessionManager.create_session(user)  # store user data in the session cache

    print('*** User data:')
    print(user_data)
    
    # Create response. Using our custom access token (not Backendless token)
    response_data = LoginResponse(
        access_token=session_token,  # Our custom token for client use
        token_type='Bearer',
        expires_in=Config.USER_IDLE_TIMEOUT,
        user=UserResponse(
            user_id=user['user_id'],
            email=user['email'],
            name=user['name'],
            account_type=user['account_type'],
            opted_in=user['opted_in'],
            is_closed=user['is_closed'],
            kb_list=kb_list,
            kb_name=kb_name
        )
    )
    
    return response_data

@router.get("/api/user/session-list/{kb_name}", response_model=list[dict])
def get_session_list(kb_name: str, 
        user_id: str = Depends(protected_user_id),
        credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get list of sessions for the current user and the specific kb_name
    Also update the current kb_name in the session cache
    """
    print(f"*** getting session list for the user {user_id} and the specific kb_name {kb_name}")
    try:
        sessions = ResearchDeskSessionSqlite.get_sessions(user_id, kb_name)
        # Use the actual session token, not the Backendless token
        session_token = credentials.credentials
        SessionManager.update_session_kb_name(session_token, kb_name)
        return sessions
    except Exception as e:
        Logger.error("Cannot get session", exception=e, report=True)
        raise HTTPException(status_code=404, detail="Failed to get sessions.")
    

@router.get("/api/user/logout", response_model=MessageResponse)
def logout(
    backendless_token: str = Depends(protected_user_token),
    credentials: HTTPAuthorizationCredentials = Depends(security) # bearer token
):
    """
    Log out the current user from the Backendless API.
    """
    # Send a request to the Backendless logout API using the Backendless token
    error, status_code = UserMgmtBackendless.logout(backendless_token)
    if error is not None:
        raise HTTPException(status_code=status_code, detail=error)

    # Remove session from cache after successful Backendless logout
    SessionManager.delete_session(credentials.credentials)
    
    return MessageResponse(message="User logged out successfully.")

@router.post("/api/user/register", response_model=MessageResponse)
def register(request: RegisterRequest):
    """
    Register a new user with the Backendless API.
    """
    print('*** User request:')
    print(request)

    # Make a request to the Backendless API to register the user
    user_data, error, status_code = UserMgmtBackendless.register(request.dict())
    if error is not None:
        raise HTTPException(status_code=status_code, detail=error)

    print('*** User data:')
    print(user_data)

    return MessageResponse(message="User registered successfully.")

@router.put("/api/user/profile", response_model=MessageResponse)
def profile(
    request: ProfileRequest,
    opted_in_changed: str | None = None,
    user_token: str = Depends(protected_user_token),
    user_id: str = Depends(protected_user_id)
):
    """
    Update user profile.
    """
    print('*** Profile request:')
    print(f' *** opted_in_changed: {opted_in_changed}')
    print(json.dumps(request.dict(exclude_none=True)))
    
    status_code = UserMgmtBackendless.profile(user_id, user_token, request.dict(exclude_none=True), opted_in_changed)
    
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail="User profile update failed.")

    return MessageResponse(message="User profile updated successfully.")

@router.delete("/api/user/close-account", response_model=MessageResponse)
def close_account(
    user_token: str = Depends(protected_user_token),
    user_id: str = Depends(protected_user_id)
):
    """
    Close user account.
    """
    status_code = UserMgmtBackendless.close_account(user_id, user_token)
    
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail="Close user account failed.")

    return MessageResponse(message="Closed user account successfully.")

@router.get("/api/user/reset/{email}", response_model=MessageResponse)
def reset(email: str):
    """
    Reset user password.
    """
    status_code = UserMgmtBackendless.reset_password(email)
    
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail="User reset password failed.")

    return MessageResponse(message="User reset password successfully.")

@router.get("/api/user/resend/{email}", response_model=MessageResponse)
def resend(email: str):
    """
    Resend verification email.
    """
    status_code = UserMgmtBackendless.resend(email)
    
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail="User resend verification email failed.")

    return MessageResponse(message="User resend verification email successfully.")

@router.get("/api/user/info", response_model=UserResponse)
def get_user_info(
    user_token: str = Depends(protected_user_token),
    user_id: str = Depends(protected_user_id)
):
    """
    Retrieve user information.
    """
    print('*** user_token: ' + user_token)
    print('*** user_id: ' + user_id)

    # Send a request to Backendless to retrieve user info based on user objectId
    user_data, error, status_code = UserMgmtBackendless.get_user_by_id(user_id, user_token)
    if error is not None:
        raise HTTPException(status_code=status_code, detail=error)
    
    # Return the user information
    print('*** User data:')
    print(user_data)
    
    return UserResponse(
        user_id=user_data['objectId'],
        email=user_data['email'],
        name=user_data['name'],
        account_type=user_data['accountType'],
        opted_in=user_data['opted_in'],
        is_closed=user_data['is_closed']
    )

@router.get("/api/user/all", response_model=AllUsersResponse)
def get_all_users(user_token: str = Depends(protected_user_token)):
    """
    Get all users from Backendless.
    """
    users, error, status_code = UserMgmtBackendless.get_all_users(user_token)
    if error is not None:
        raise HTTPException(status_code=status_code, detail=error)
    
    return AllUsersResponse(users=users)

@router.get("/api/user/{user_id}", response_model=dict)
def get_user_by_id(
    user_id: str,
    user_token: str = Depends(protected_user_token)
):
    """
    Get user by ID from Backendless.
    """
    user, error, status_code = UserMgmtBackendless.get_user_by_id(user_id, user_token) 
    if error is not None:
        raise HTTPException(status_code=status_code, detail=error)
    
    return user

@router.post("/api/contact", response_model=MessageResponse)
def contact(
    request: ContactRequest,
    user_id: str = Depends(protected_user_id),
    kb_name: str = Depends(protected_user_kb_name)
):
    """
    Store contact message in the database.
    """
    print('*** Contact request:')
    print(request)

    # Make a request to store the contact message
    isError = ContactSqlite.contact(user_id, request.dict(), kb_name)
    if isError:
        raise HTTPException(status_code=500, detail="Failed to insert contact message into the database.")

    print({'message': 'Contact saved successfully.'})

    return MessageResponse(message="Contact saved successfully.")

@router.post("/api/share", response_model=MessageResponse)
def share(
    request: ShareRequest,
    emails: str,
    user_token: str = Depends(protected_user_token),
    user_email: str = Depends(protected_user_email)
):
    """
    Share via email route.
    """
    share_request = request.dict()
    share_request['handle'] = user_email
    print('*** Share request:')
    print(share_request)
    
    emails = emails.replace(" ", "")  # remove spaces from emails:
    emails = emails.split(',')  # split the email list by comma
    share_request['categories'] = ', '.join(share_request['categories'])  # convert the categories list to a string
    status = NotificationService.send('Share', emails, share_request, user_token)

    if status != 200:
        raise HTTPException(status_code=status, detail="Failed to send share email.")
    
    return MessageResponse(message="Share email sent successfully.")

@router.put("/api/user/change-password", response_model=MessageResponse)
def change_password(
    request: ChangePasswordRequest,
    user_token: str = Depends(protected_user_token), 
    user_id: str = Depends(protected_user_id)
):
    """
    Change user password.
    """
    status_code = UserMgmtBackendless.change_password(user_id, user_token, request.new_password)
    
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail="Change user password failed.")

    return MessageResponse(message="User password changed successfully.")
