from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
from rest_framework import status
from rest_framework.request import Request
from ..auth import spotify_api as api
from django.contrib.auth import authenticate
from ..models.user import UserTokenDataSerializer, get_token_for_user
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from ..auth.spotify_api import get_user_info, refresh_token_info
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
                            status=status.HTTP_401_UNAUTHORIZED)

    if settings.DEBUG:
        print(ser.validated_data)
    # If this user's credentials doesn't contain spotify credentials, just return it.
    if not spotify_params['access_token'] or not spotify_params[
            'refresh_token']:
        return JsonResponse(ser.validated_data)

    # Check and refresh user's spotify token
    try:
        response = get_user_info(spotify_params)
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
    except pyrequests.RequestException:
        pass
    try:
        refresh_response = refresh_token_info(spotify_params)
        spotify_params['access_token'] = refresh_response['access_token']
        spotify_params['refresh_token'] = refresh_response['refresh_token']
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
    except pyrequests.RequestException:
        return JsonResponse({'error': 'Refresh Token is Invalid'},
                            status=status.HTTP_401_UNAUTHORIZED)
