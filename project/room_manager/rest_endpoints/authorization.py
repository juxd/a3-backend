from rest_framework.decorators import api_view
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
from ..auth import spotify_api as api
from django.contrib.auth import authenticate
from ..models.user import UserTokenDataSerializer, get_token_for_user
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
import json


@api_view(["GET"])
def initiate(request):
    response = redirect(api.AUTH_CODE_REQUEST_URL)
    return response


@api_view(["GET"])
def exchange_token(request):
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
def refresh_token(request):
    if settings.DEBUG:
        print(json.loads(request.body))
    # Refresh user's token
    ser = TokenRefreshSerializer(data=json.loads(request.body))
    ser.is_valid()
    if settings.DEBUG:
        print(ser.validated_data)
    # Check and refresh user's spotify token
    return JsonResponse(ser.validated_data)
