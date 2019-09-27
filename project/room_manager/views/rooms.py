from ..models import Room
from ..models.user import UserShareableSerializer
from ..models.room import RoomSerializer, RoomOwnerPermission
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.serializers import CurrentUserDefault
from django.http import JsonResponse
from django.conf import settings
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny


class RoomViewSet(viewsets.ModelViewSet):
    """
    ViewSets are analagous to Rails controllers.
    Each viewset to correspond to a resource name, and Django-rest would
    generate some default routes to model mutations.
    Find out more at: https://www.django-rest-framework.org/api-guide/viewsets/
    """
    queryset = Room.objects.filter(alive=1).all()
    serializer_class = RoomSerializer

    def retrieve(self, request, pk=None):
        """
        Override room retrieval to access by its unique_identifier,
        instead of its primary key (which is its running id.)
        """
        room = get_object_or_404(Room, unique_identifier=pk, alive=1)
        serializer = self.get_serializer(room)
        data = dict(serializer.data, status=status.HTTP_200_OK)

        user = request.user
        if user.is_anonymous:
            isHost = False
        else:
            isHost = user.identifier == Room.get_owner_id_if_exists(data['unique_identifier'])
        data['isHost'] = isHost

        return JsonResponse(data)

    def destroy(self, request, pk=None):
        room = get_object_or_404(Room, unique_identifier=pk)
        room.kill()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, pk=None):
        serializer = self.get_serializer(data=request.data,
                                         context={'request': request})
        serializer.is_valid()
        self.perform_create(serializer)
        request.user.set_device_id(request.data['device_id'])
        headers = self.get_success_headers(serializer.data)
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)

    def get_permissions(self):
        """
        Here we define the permissions required to access resources,
        depending on the action.
        For the room viewset, everything except for the list (get all)
        method would require the user to be authenticated.
        For actions that mutate the room such as updates and destroys,
        you need to be the room owner.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        elif self.action in ['update', 'destroy', 'partial_update']:
            permission_classes = [RoomOwnerPermission]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
