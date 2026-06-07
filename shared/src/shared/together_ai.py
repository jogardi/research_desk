import requests
from dotenv import load_dotenv
import os

load_dotenv()

TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')
TOGETHER_API_URL = "https://api.together.xyz/v1/"

def together_headers():
    return {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {TOGETHER_API_KEY}"
    }

def together_post_json(uri, obj):
    return requests.post(TOGETHER_API_URL + uri, headers=together_headers(), json=obj)


