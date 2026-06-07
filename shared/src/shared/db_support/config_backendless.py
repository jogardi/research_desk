import json
import os
import sys
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

BACKENDLESS_SERVER_URL = f"{os.environ.get('BACKENDLESS_SERVER')}/{os.environ.get('BACKENDLESS_APP_ID')}/{os.environ.get('BACKENDLESS_API_KEY')}"

class ConfigBackendless:
    @staticmethod
    def login():
        user_credentials = {
            "login": os.environ.get('FLAG_USER_ID'),
            "password": os.environ.get('FLAG_PASSCODE')
        }

        
        try:
            response = requests.post(f"{BACKENDLESS_SERVER_URL}/users/login", json=user_credentials)
        except Exception as e:
            print(f"Backendless login failed: {e}")
            sys.exit(1)
         
        
        if (response.status_code != 200):
            print(f"Backendless user login failed: {response.text} {response.status_code}")
            sys.exit(1)
        
        return response.json()
    
    
    @staticmethod
    def get_config(org_name, profile_name) -> dict:
        login_response = ConfigBackendless.login()
        
        user_token = login_response['user-token']
        
        response = requests.get(f"{BACKENDLESS_SERVER_URL}/data/HPARAM_PROFILE_CFG?where=org_name='{org_name}' and profile_name='{profile_name}'", headers={'user-token': user_token})
        if (response.status_code != 200):
            print(f"Backendless get config failed: {response.text}")
            sys.exit(1)
            
        hparam_data = response.json()[0]
        
        response = requests.get(f"{BACKENDLESS_SERVER_URL}/data/ORG_CFG?where=org_name='{org_name}'", headers={'user-token': user_token})
        if (response.status_code != 200):
            print(f"Backendless get config failed: {response.text}")
            sys.exit(1)
       
        org_data = response.json()[0]
        
        response = requests.get(f"{BACKENDLESS_SERVER_URL}/data/PROFILE_CFG?where=org_name='{org_name}' and profile_name='{profile_name}'", headers={'user-token': user_token})
        if (response.status_code != 200):
            print(f"Backendless get config failed: {response.text}")
            sys.exit(1)
       
        profile_data = response.json()[0]
        
        response = requests.get(f"{BACKENDLESS_SERVER_URL}/data/KB_CFG?where=org_name='{org_name}'", headers={'user-token': user_token})
        if (response.status_code != 200):
            print(f"Backendless get config failed: {response.text}")
            sys.exit(1)
       
        kb_data = response.json()
        
        
        
        config_data = {**hparam_data, **org_data, **profile_data}
        
       
        config_data["KNOWLEDGEBASES_DATA"] = kb_data
        #config_data["kb_data"] = kb_data  # Also add as kb_data for direct access
        
        # Remove 'cfg_' prefix from attribute names in config_data and knowledgebases_data
        config_data = {key[4:].upper() if key.startswith('cfg_') else key.upper(): value for key, value in config_data.items()}
        config_data["KNOWLEDGEBASES_DATA"] = [
            {key[4:].upper() if key.startswith('cfg_') else key.upper(): value for key, value in kb.items()}
            for kb in config_data["KNOWLEDGEBASES_DATA"]
        ]
        
        return config_data
        
        
        
        
        
        
    
    

