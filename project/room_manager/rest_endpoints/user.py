from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.http import JsonResponse


@api_view(["GET", "POST"])
def device(request):
    if request.method == 'POST':
        # TODO: Identify user and write to database
        # Access body with request.data
        return Response(status=status.HTTP_202_ACCEPTED)
