from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import json
from shared.logger import Logger 
from webservice.routes.oauth_factory import OAuthFactory
from webservice.persistence.user_mgmt_backendless import UserMgmtBackendless 
from shared.config import Config
from webservice.routes.social_loginCache import SocialLoginCache
from webservice.session_manager import SessionManager
from webservice.schemas.social_login import SocialLoginFinishResponse
from webservice.schemas.user import UserResponse

# FastAPI Router for all social login routes
router = APIRouter(tags=["social_login"])

# Route for starting the OAuth login flow
@router.get("/login/{provider}")
def login(provider: str, request: Request):
    """Start the OAuth login flow for the specified provider."""
    print(f"*** Starting OAuth login flow for provider '{provider}'")
    try:
        # Dynamically create the redirect URI for the selected provider
        # Note: In FastAPI, we need to use the function name, not the route name
        redirect_uri = str(request.url_for('authorize', provider=provider))
        print(f"*** Redirect URI: {redirect_uri}")
        # Initiate the OAuth login flow by redirecting the user to the provider's login page
        oauth_client = OAuthFactory.get_client(provider)
        print("*** Redirecting to the provider's login page...")
        
        # Get the authorization URL from the OAuth client
        authorization_url, _ = oauth_client.create_authorization_url(redirect_uri)
        print(f"*** Authorization URL: {authorization_url}")
        
        # Return a redirect response
        return RedirectResponse(url=authorization_url)
    except Exception as e:
        Logger.error(f"Failed to start OAuth login flow for provider '{provider}': ", exception=e)
        return create_close_window_script({ "error": f"Failed to start OAuth login flow for provider '{provider}'" })

# Route to handle the provider's callback with the authorization code
@router.get("/authorize/{provider}")
def authorize(provider: str):
    """Handle the provider's callback with the authorization code."""
    print(f"*** Provider '{provider}' callback received.")
    try:
        # Create the OAuth client for the selected provider
        oauth_client = OAuthFactory.get_client(provider)

        # Retrieve the access token from the provider
        access_token = oauth_client.authorize_access_token()
        Logger.info(f"*** Access token: {json.dumps(access_token)}")
        # Parse user information from the token (Google requires parsing of the ID token)
        if provider == 'google' or provider == 'twitter':
            access_token = access_token['access_token']

        user_data, error, status_code = UserMgmtBackendless.social_login(provider, access_token)
        if error is not None:
            return create_close_window_script(error)

        print('*** User data from backendless:')
        print(user_data)

        # Store the user data in the cache
        user_id = user_data['objectId']
        SocialLoginCache.store(user_id, user_data) # Store the user data in the cache with the user_id as the key

        return create_close_window_script({ 'token': user_id})
    except Exception as e:
        Logger.error(f"Failed to authorize user with provider '{provider}': ", exception=e)
        return create_close_window_script({ "error": f"Failed to authorize user with provider '{provider}'" })

# Helper function to create a script that sends data to the parent window and closes the popup    
def create_close_window_script(data):
    """Create HTML script that sends data to parent window and closes popup."""
    return HTMLResponse(content=f'''
        <script>
            window.opener.postMessage({json.dumps(data)}, "*"); // will need to replace "*" with the parent origin        
            window.close();
        </script>
    ''')

# Route to handle the callback from the parent window
@router.get("/login/finish/{user_id}", response_model=SocialLoginFinishResponse)
def login_finish(user_id: str):
    """Finish the login process by retrieving cached user data and creating session."""
    print(f"*** Finishing login process. User ID: {user_id}")
    # Retrieve the user data from the cache
    user_data = SocialLoginCache.retrieve(user_id)
    if user_data is None:
        raise HTTPException(status_code=401, detail="User login expired!")
    
    user = {
        'user_id': user_data['objectId'],
        'backendless_token': user_data['user-token'],  # Backendless token for internal use
        'email': user_data['email'],
        'name': user_data['name'],
        'account_type': user_data['accountType'],
        'opted_in': user_data['opted_in'],
        'is_closed': user_data['is_closed']
    }

    # Create session and get our custom access token (same as regular login)
    access_token = SessionManager.create_session(user)

    # Create response similar to regular login
    response_data = SocialLoginFinishResponse(
        access_token=access_token,  # Our custom token for client use
        token_type='Bearer',
        expires_in=Config.USER_IDLE_TIMEOUT,
        user=UserResponse(
            user_id=user['user_id'],
            email=user['email'],
            name=user['name'],
            account_type=user['account_type'],
            opted_in=user['opted_in'],
            is_closed=user['is_closed']
        )
    )
    
    return response_data