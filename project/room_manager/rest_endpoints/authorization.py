from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
from rest_framework.request import Request
from ..auth import spotify_api as api
from django.contrib.auth import authenticate
from ..models.user import UserTokenDataSerializer, get_token_for_user
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
import json
import requests as pyrequests


@api_view(["GET"])
def initiate(request: Request) -> JsonResponse:
    response = redirect(api.AUTH_CODE_REQUEST_URL)
    return response


@api_view(["GET"])
def exchange_token(request: Request) -> JsonResponse:
    if settings.DEBUG:
        print(dict(request.query_params))
    user = authenticate(request, **dict(request.query_params))
    if user is not None:
        app_tokens = get_token_for_user(user)
        app_tokens['spotify_access_token'] = user.access_token
        app_tokens['spotify_refresh_token'] = user.refresh_token
        return JsonResponse(app_tokens)
    return JsonResponse({'error': 'Invalid Request'}, status=401)


@api_view(["POST"])
def refresh_token(request: Request) -> JsonResponse:
    """
    Refreshes a user's token info. They should contain:
     - Access token
     - Refresh token
     - Spotify access token (optional)
     - Spotify refresh token (if spotify access token is provided).
    """
    if settings.DEBUG:
        print(json.loads(request.body))
    # Refresh user's token
    body = json.loads(request.body)
    spotify_params = {}
    spotify_params['access_token'] = body.pop('spotify_access_token', '')
    spotify_params['refresh_token'] = body.pop('spotify_refresh_token', '')
    try:
        ser = TokenRefreshSerializer(data=body)
        ser.is_valid()
    except TokenError:
        # Request is not valid.
        return JsonResponse({'error': 'Refresh Token is Invalid'},
                            status_code=401)
    if settings.DEBUG:
        print(ser.validated_data)
    # If this user's credentials doesn't contain spotify credentials, just return it.
    if not spotify_params['access_token'] or not spotify_params[
            'refresh_token']:
        return JsonResponse(ser.validated_data)

    # Check and refresh user's spotify token
    headers = {'Authorization': 'Bearer ' + spotify_params['access_token']}
    response = pyrequests.get('https://api.spotify.com/v1/me', headers=headers)
    if response.status_code >= 400:
        params = {
            'grant_type': 'authorization_code',
            'client_id': settings.CLIENT_ID,
            'client_secret': settings.CLIENT_SECRET,
            'code': spotify_params['refresh_token'],
            'redirect_uri': 'http://127.0.0.1:3000/'
        }
        sresponse = pyrequests.post('https://accounts.spotify.com/api/token',
                                    params=params)
        if settings.DEBUG:
            print(sresponse.text)
        spotify_params['access_token'] = json.loads(
            sresponse.text)['access_token']
        spotify_params['refresh_token'] = json.loads(
            sresponse.text)['refresh_token']
    return JsonResponse({
        'access_token':
        ser.validated_data['access'],
        'refresh':
        body['refresh'],
        'spotify_access_token':
        spotify_params['access_token'],
        'spotify_refresh_token':
        spotify_params['refresh_token']
    })
