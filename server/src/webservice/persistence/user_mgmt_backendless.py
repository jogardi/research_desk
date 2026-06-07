import json
import os
import requests
from datetime import datetime, timezone
from shared.config import Config
from shared.logger import Logger

# set the backendless server URL
BACKENDLESS_SERVER_URL = f"{os.environ.get('BACKENDLESS_SERVER')}/{os.environ.get('BACKENDLESS_APP_ID')}/{os.environ.get('BACKENDLESS_API_KEY')}"

class UserMgmtBackendless:
    @staticmethod
    def login(user_credentials):
        """
        Login a user with the Backendless API.

        Parameters:
            user_credentials (dict): The user credentials to login.

        Returns: (user_data, None, None) or (None, error, status_code)
        """
        
        try:
            response = requests.post(f"{BACKENDLESS_SERVER_URL}/users/login", json=user_credentials)
        except Exception as e:
            Logger.error("Backendless login failed", exception=e)
            return None, {'error': 'Exception: Backendless login failed'}, 500
        
        if (response.status_code != 200):
            Logger.error("Backendless user login failed", response=response)
            return None, {'error': f'Response: Backendless user login failed: : {response.text}'}, response.status_code
        
        return response.json(), None, None # user_data
    
    @staticmethod
    def social_login(provider, access_token):
        provider_code = 'googleplus' if provider == 'google' else provider # Backendless uses 'googleplus' for Google
        payload = {  
            "accessToken": access_token,  
            # "fieldsMapping": JSON,  
            }
        try:
            response = requests.post(f"{BACKENDLESS_SERVER_URL}/users/oauth/{provider_code}/login", json=payload)
        except Exception as e:
            Logger.error("Backendless social login failed", exception=e)
            return None, {'error': 'Exception: Backendless social login failed'}, 500
        
        if (response.status_code != 200):
            Logger.error("Backendless social login failed", response=response)
            return None, {'error': 'Response: Backendless social login failed'}, response.status_code
        
        return response.json(), None, None
    
    @staticmethod
    def register(user_payload):
        """
        Register a user with the Backendless API.

        Parameters:
            user_payload (dict): The user payload to register.

        Returns: (user_data, error, status_code) or (None, error, status_code)
        """
        
        try:
            response = requests.post(f"{BACKENDLESS_SERVER_URL}/users/register", json=user_payload)
        except Exception as e:
            Logger.error("Backendless user registration failed", exception=e)
            return None, {'error': 'Backendless register failed'}, 500
        
        if (response.status_code != 200):
            Logger.error("Backendless user registration failed", response=response)
            return None, {'error': f'Response: Backendless user registration failed: {response.text}'}, response.status_code
        
        return response.json(), None, None # user_data
    
    @staticmethod
    def reset_password(email):   
        try:
            response = requests.get(f"{BACKENDLESS_SERVER_URL}/users/restorepassword/{email}")
        except Exception as e:
            Logger.error("Backendless reset password failed", exception=e)
            return 500
        
        if (response.status_code != 200):
            Logger.error("Backendless reset password failed", response=response)
            return 500
        
        return 200
    
    @staticmethod
    def resend(email):   
        try:
            response = requests.post(f"{BACKENDLESS_SERVER_URL}/users/resendconfirmation/{email}")
        except Exception as e:
            Logger.error("Backendless resend verification email failed", exception=e)
            return 500
        
        if (response.status_code != 200):
            Logger.error("Backendless resend verification email failed", response=response)
            return 500
        
        return 200
    
    @staticmethod
    def profile(user_id, user_token, profile_payload, opted_in_changed):
        if (opted_in_changed == 'true'):
            now = datetime.now(timezone.utc) # Get the current date and time
            timestamp = int(now.timestamp() * 1000) # Convert the timestamp to milliseconds since epoch
            profile_payload['opted_time_stamp'] = timestamp
        try:
            response = requests.put(f"{BACKENDLESS_SERVER_URL}/data/Users/{user_id}",  headers={'user-token': user_token}, json=profile_payload)
        except Exception as e:
            Logger.error("Backendless user profile update failed", exception=e)
            return 500
        
        if (response.status_code != 200):
            Logger.error("Backendless user profile update failed", response=response)
            return response.status_code
        
        return 200
    
    @staticmethod
    def close_account(user_id, user_token):
        now = datetime.now(timezone.utc) # Get the current date and time
        timestamp = int(now.timestamp() * 1000) # Convert the timestamp to milliseconds since epoch
        payload = {
            "closed_time_stamp": timestamp,
            "is_closed": True
        }
        try:
            response = requests.put(f"{BACKENDLESS_SERVER_URL}/data/Users/{user_id}",  headers={'user-token': user_token}, json=payload)
        except Exception as e:
            Logger.error("Backendless close account failed", exception=e)
            return 500
        
        if (response.status_code != 200):
            Logger.error("Backendless user close account failed", response=response)
            return response.status_code
        
        return 200
    
    @staticmethod
    def logout(user_token):
        """
        Logout the user from the Backendless API.

        Parameters:
            user_token (str): The user token to logout.

        Returns: (None, None) or (error, status_code)
        """
        try:
            response = requests.get(f"{BACKENDLESS_SERVER_URL}/users/logout", headers={'user-token': user_token})
        except Exception as e:
            Logger.error("Backendless logout failed", exception=e)
            return {'error': 'Exception: Backendless logout failed'}, 500
        
        if (response.status_code != 200):
            Logger.error("Backendless logout failed", response=response)
            return {'error': 'Response: Backendless logout failed'}, response.status_code
        
        return None, None

    @staticmethod
    def validate_token(user_token):
        """
        Validate the user token with the Backendless API.
        
        Parameters:
            user_token (str): The user token to validate.
            
            Returns: (True, None, None) or (False, None, None) or (None, error, status_code)
        """
        try:
            response = requests.get(f"{BACKENDLESS_SERVER_URL}/users/isvalidusertoken/{user_token}")
        except Exception as e:
            Logger.error("Backendless validate token failed", exception=e)
            return None, {'error': 'Exception: Backendless validate token failed'}, 500
        
        if (response.status_code != 200):
            Logger.error("Backendless validate token failed", response=response)
            return None, {'error': 'Response: Backendless validate token failed'}, response.status_code
        
        return response.json(), None, None # True or False
    
    @staticmethod
    def get_app_user(email, user_token):
        try:
            response = requests.get(f"{BACKENDLESS_SERVER_URL}/data/APP_USER?where=email='{email}' and org='{Config.ORG_NAME}'", headers={'user-token': user_token})
        except Exception as e:
            Logger.error("Backendless get app user failed", exception=e)
            return None, {'error': 'Exception: Backendless get app user failed'}, 500
        
        if (response.status_code != 200):
            Logger.error("Backendless get app user failed", response=response)
            return None, {'error': 'Response: Backendless get app user failed'}, response.status_code
        
        data = response.json()
        # Return the first dict if found, otherwise None
        if data and len(data) > 0:
            return data[0], None, None
        else:
            return None, None, None
    
    @staticmethod
    def get_all_users(user_token):
        """
        Get all users from the Backendless API.
            
        Returns: (users, None, None) or (None, error, status_code)
        """
        try:
            response = requests.get(f"{BACKENDLESS_SERVER_URL}/data/Users", headers={'user-token': user_token})
        except Exception as e:
            Logger.error("Backendless get all users failed", exception=e)
            return None, {'error': 'Exception: Backendless get all users failed'}, 500
        
        if (response.status_code != 200):
            Logger.error("Backendless get all users failed", response=response)
            return None, {'error': 'Response: Backendless get all users failed'}, response.status_code
        
        return response.json(), None, None # users
    
    @staticmethod
    def get_user_by_id(user_id, user_token):
        try:
            response = requests.get(f"{BACKENDLESS_SERVER_URL}/data/Users/{user_id}", headers={'user-token': user_token})
        except Exception as e:
            Logger.error("Backendless get user by ID failed", exception=e)
            return None, {'error': 'Exception: Backendless get user by ID failed'}, 500
        
        if (response.status_code != 200):
            Logger.error("Backendless get user by ID failed", response=response)
            return None, {'error': 'Response: Backendless get user by ID failed'}, response.status_code
        
        return response.json(), None, None
    
    @staticmethod
    def update_external_api_count(user_id, user_token, external_api_count):
        payload = {
            "external_api_count": external_api_count
        }
        try:
            response = requests.put(f"{BACKENDLESS_SERVER_URL}/data/Users/{user_id}",  headers={'user-token': user_token}, json=payload)
        except Exception as e:
            Logger.error("Backendless update external API count failed", exception=e)
            return 500
        
        if (response.status_code != 200):
            Logger.error("Backendless update external API count failed", response=response)
            return response.status_code
        
        return 200
    
    @staticmethod
    def change_password(user_id, user_token, new_password):
        payload = {
            "password": new_password
        }
        try:
            response = requests.put(f"{BACKENDLESS_SERVER_URL}/data/Users/{user_id}", headers={'user-token': user_token}, json=payload)
        except Exception as e:
            Logger.error("Backendless update password failed", exception=e)
            return 500
        
        if (response.status_code != 200):
            Logger.error("Backendless update password failed", response=response)
            return response.status_code
        
        return 200
    
    


