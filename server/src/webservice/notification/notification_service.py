import os
import json
import requests

from typing import List
#from dotenv import load_dotenv

from shared.config import Config
from shared.logger import Logger

# set the backendless server URL
#load_dotenv()
BACKENDLESS_URL = f"{os.environ.get('BACKENDLESS_SERVER')}/{os.environ.get('BACKENDLESS_APP_ID')}/{os.environ.get('BACKENDLESS_NOTIFICATION_API_KEY')}/emailtemplate/send"


class NotificationService(): 
    
    @staticmethod
    def send( template_name: str, emails: List, body: dict, user_token: str) -> int:      
        
        try:
            response = requests.post(f"{BACKENDLESS_URL}", json={'template-name': template_name, 'addresses': emails,
                                                                 'template-values': body}, 
                                     headers={'user-token': user_token})
        except Exception as e:
            Logger.error(f"Backendless send error for {template_name}: {str(e)}")
            return 500
        
        if (response.status_code != 200):
            Logger.error(f"Backendless send error for {template_name}: {response.status_code} {response.text}")
            return response.status_code
        
        return 200
    
    
def process():
    # test the notification service
    emails = ['recipient@example.com']
    body = {'handle': 'handle', 'categories': 'cats', 'search_query': 'ss',  'summary': 'summary', 'aillm_query': 'query', 'aillm_response': 'response'}    
    user_token = os.environ.get('BACKENDLESS_USER_TOKEN', '')
    template_name = 'Share'
    response = NotificationService.send(template_name, emails, body, user_token)    
    print(response)



if __name__ == '__main__':
    process()
