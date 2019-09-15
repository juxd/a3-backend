from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import redirect
import urllib.parse as urlparse
import requests as pyrequests
import json

#TODO: abstract to constants file
REDIRECT_URI = "http://127.0.0.1:8000/authorize/done/"
CLIENT_ID = "199ea20d5b2643688e8d3ad38ea61bf2"
CLIENT_SECRET = "badaa3c651eb43b080da0ecfc2ed960c"
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


@api_view(["GET"])
def initiate(request):
    base_url = SPOTIFY_EXCHANGE_URI
    query_string = urlparse.urlencode({
        "client_id" : CLIENT_ID, 
        "response_type" : "code", 
        "redirect_uri" : REDIRECT_URI, 
        "scope" : SCOPES})
    url = "{}?{}".format(base_url, query_string)
    response = redirect(url)
    return response
        

@api_view(["GET"])
def exchange_token(request):
    spotify_response = request.query_params
    query = dict(spotify_response)
    
    if ('error' in query):
        # TODO: process authorizatiion failure
        raise RuntimeError("Authorization failure")

    code = query['code']
    # state = query['state']
    # TODO: verify that state corresponds to what we supplied to spotify
    
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    response = pyrequests.post('https://accounts.spotify.com/api/token', data=data)

    # TODO: Handle invalid response
    json_data = json.loads(response.text)

    #TODO: Write to DB
    print(json_data)

    # WARNING: quick hack to return access token & refresh token in query parameters since there's no user model yet
    redirect_url = f"{REDIRECT_FRONT_END_URI}?access_token={json_data['access_token']}&expires_in={json_data['expires_in']}&refresh_token={json_data['refresh_token']}"
    return redirect(redirect_url)



