from flask import Flask
from authlib.integrations.flask_client import OAuth
import os

class OAuthFactory:
    _instance = None

    @classmethod
    def initialize(cls, app: Flask):
        cls._instance = OAuth(app)

        # Register Google OAuth
        # cls._instance.register(
        #     name='google',
        #     client_id=os.getenv('GOOGLE_CLIENT_ID'),
        #     client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        #     authorize_url='https://accounts.google.com/o/oauth2/auth',
        #     authorize_params=None,
        #     access_token_url='https://accounts.google.com/o/oauth2/token',
        #     access_token_params=None,
        #     client_kwargs={'scope': 'openid email profile'},
        # )

        cls._instance.register(
            name='google',
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',  # Use Google's OpenID Connect discovery URL
            client_kwargs={'scope': 'openid email profile'},
        )

        cls._instance.register(
            name='facebook',
            client_id=os.getenv('FACEBOOK_CLIENT_ID'),
            client_secret=os.getenv('FACEBOOK_CLIENT_SECRET'),
            authorize_url='https://www.facebook.com/v12.0/dialog/oauth',
            authorize_params=None,
            access_token_url='https://graph.facebook.com/v12.0/oauth/access_token',
            access_token_params=None,
            client_kwargs={'scope': 'email public_profile'},
        )

        cls._instance.register(
            name='twitter',
            client_id=os.getenv('TWITTER_CLIENT_ID'),
            client_secret= os.getenv('TWITTER_CLIENT_SECRET'),
            authorize_url='https://twitter.com/i/oauth2/authorize',
            access_token_url='https://api.twitter.com/2/oauth2/token',
            client_kwargs={
                'scope': 'tweet.read users.read offline.access',
                'token_endpoint_auth_method': 'client_secret_basic',
                'code_challenge_method': 'S256',
            },
        )

    @classmethod
    def get_client(cls, provider: str):
        if (cls._instance is None):
            raise Exception("OAuthFactory not initialized")
        return cls._instance.create_client(provider)