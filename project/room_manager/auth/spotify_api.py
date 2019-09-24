from django.conf import settings
from typing import Dict, Union
import urllib.parse as urlparse
import requests as pyrequests
import json
import base64
"""
Helper methods to access the spotify API
"""
REDIRECT_URI = settings.PATH_TO_FRONTEND + "/signin/callback/"
SPOTIFY_EXCHANGE_URI = "https://accounts.spotify.com/authorize"

SPOTIFY_ALLOWED_SCOPES = { # We can untick/unset some of these more easily later on.
    'user-modify-playback-state'  : True,
    'user-read-playback-state'    : True,
    'user-read-currently-playing' : True,
    'user-top-read'               : True,
    'user-read-recently-played'   : True,
    'user-library-modify'         : True,
    'user-library-read'           : True,
    'user-follow-modify'          : True,
    'user-follow-read'            : True,
    'playlist-read-private'       : True,
    'playlist-modify-public'      : True,
    'playlist-modify-private'     : True,
    'playlist-read-collaborative' : True,
    'user-read-private'           : True,
    'user-read-email'             : True,
    'app-remote-control'          : True,
    'streaming'                   : True,
}
REDIRECT_FRONT_END_URI = settings.PATH_TO_FRONTEND + "/signin/callback"

AUTH_CODE_REQUEST_PARAMS = {
    "client_id": settings.CLIENT_ID,
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": ' '.join([k for k, v in SPOTIFY_ALLOWED_SCOPES.items() if v])
}

AUTH_CODE_REQUEST_URL = "{}?{}".format(
    SPOTIFY_EXCHANGE_URI, urlparse.urlencode(AUTH_CODE_REQUEST_PARAMS))

def _b64encoded(client_id: str, client_secret: str) -> str:
    raw_credentials = '%s:%s' % (client_id, client_secret)
    encoded_bytes = base64.b64encode(raw_credentials.encode('utf-8'))
    encoded_string = str(encoded_bytes, 'utf-8')
    print('encoded', encoded_string)
    return encoded_string

ENCODED_CREDENTIALS = _b64encoded(settings.CLIENT_ID, settings.CLIENT_SECRET)

def get_token(auth_code: str = '') -> Dict[str, Union[int, str]]:
    """
        Returns a dictionary of all related information to be used for token authentication.
        Check them out here:
        https://developer.spotify.com/documentation/general/guides/authorization-guide/
        """
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'client_id': settings.CLIENT_ID,
        'client_secret': settings.CLIENT_SECRET
    }
    response = pyrequests.post('https://accounts.spotify.com/api/token',
                               data=data)
    if response.status_code >= 400:
        raise pyrequests.RequestException('Authorisation Failed')
    return json.loads(response.text)


def get_user_info(token: Dict[str, str]) -> Dict[str, str]:
    headers = {'Authorization': 'Bearer ' + token['access_token']}
    if settings.DEBUG:
        print(headers)
    response = pyrequests.get('https://api.spotify.com/v1/me', headers=headers)
    if response.status_code >= 400:
        raise pyrequests.RequestException('Request Failed')
    return json.loads(response.text)


def refresh_token_info(token: Dict[str, str]) -> Dict[str, str]:
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': token['refresh_token'],
    }
    headers = { 'Authorization': f'Basic {ENCODED_CREDENTIALS}' }
    sresponse = pyrequests.post('https://accounts.spotify.com/api/token',
                                headers=headers,
                                data=data)
    if settings.DEBUG:
        print(data)
        print(headers)
        print(sresponse.text)
    if sresponse.status_code >= 400:
        raise pyrequests.RequestException('Request Failed')
    res = json.loads(sresponse.text)
    res['refresh_token'] = token['refresh_token']
    return res


#TODO: write decorator for retry pattern.
