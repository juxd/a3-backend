from rest_framework.decorators import api_view
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
from ..auth import spotify_api as api
from django.contrib.auth import authenticate
from ..models.user import UserTokenDataSerializer


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
        serialized_user = UserTokenDataSerializer(user)
        return JsonResponse(serialized_user.data, status=201)
    return JsonResponse({'error': 'Invalid Request'}, status=401)
