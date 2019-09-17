from rest_framework import api_view
from rest_framework import Response, Request
from project.room_manager.models import User
from django.conf.settings import CLIENT_ID, CLIENT_SECRET
from typing import Dict
import requests as pyrequests

class SpotifyBackend:
    def authenticate(self,
                     request: Request,
                     error: str,
                     code: str,
                     state: str) -> User:
        #TODO: check state for request validity
        if error:
            return None
        try:
            token_data = get_token(code)
            user_info = get_user_info(token_data)
            user, _ = User.find_or_create_user(user_info, token_data)
            return user
        except:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

class SpotifyAuthApis:
    """
    Helper methods to access the spotify API
    """
    REDIRECT_URI = "http://127.0.0.1:8000/authorize/done/"
    SPOTIFY_EXCHANGE_URI = "https://accounts.spotify.com/authorize"
    SCOPES = "\
user-modify-playback-state \
user-read-playback-state \
user-read-currently-playing \
user-top-read \
user-read-recently-played \
user-library-modify \
user-library-read \
user-follow-modify \
user-follow-read \
playlist-read-private \
playlist-modify-public \
playlist-modify-private \
playlist-read-collaborative \
user-read-private \
user-read-email \
app-remote-control \
streaming"
    REDIRECT_FRONT_END_URI = "http://localhost:3000/signin/callback"

    @staticmethod
    def get_token(auth_code: str) -> Dict[str, Union[int,str]]:
        """
        Returns a dictionary of all related information to be used for token authentication.
        Check them out here:
        https://developer.spotify.com/documentation/general/guides/authorization-guide/
        """
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        response = pyrequests.post('https://accounts.spotify.com/api/token', data=data)
        if response.status_code >= 400:
            raise pyrequests.RequestException('Authorisation Failed')
        return json.loads(response.text)

    @staticmethod
    def get_user_info(token: Dict[str, str]) -> Dict[str, str]:
        headers = {'Authorization':token['access_token']}
        response = pyrequests.get('https://api.spotify.com/v1/me', headers=headers)
        if response.status_code >= 400:
            raise pyrequests.RequestException('Request Failed')
        return json.loads(response.text)

    #TODO: write decorator for retry pattern.
