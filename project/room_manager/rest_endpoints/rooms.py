from ..models import Room
from ..models.room import RoomSerializer
from django.conf import settings
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from django.http import JsonResponse


@api_view(["GET"])
def all_rooms(request: Request) -> JsonResponse:
    serializer = RoomSerializer(Room.objects.all(), many=True)
    if settings.DEBUG:
        print(serializer.data)
    return JsonResponse(serializer.data, safe=False)

@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create(request):
    print(request.body)
    # TODO: Create room in backend and return it in roomId
    return JsonResponse({'roomId': '123abc'}, status=201)
