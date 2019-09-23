from ..models import Room
from ..models.room import RoomSerializer
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from django.http import JsonResponse


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def all_rooms(request: Request) -> JsonResponse:
    serializer = RoomSerializer(Room.objects.all(), many=True)
    return JsonResponse(serializer.data)
