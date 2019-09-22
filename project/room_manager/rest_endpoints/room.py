from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.http import JsonResponse

@api_view(["POST"])
def create(request):
    if request.method == 'POST':
        # TODO: Create room in backend and return it in roomId
        return JsonResponse({'roomId': '123abc'}, status=201)
