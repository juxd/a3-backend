from ..models import Room
from ..models.room import RoomSerializer
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny



class RoomViewSet(viewsets.ModelViewSet):
    """
    ViewSets are analagous to Rails controllers.
    Each viewset to correspond to a resource name, and Django-rest would
    generate some default routes to model mutations.
    Find out more at: https://www.django-rest-framework.org/api-guide/viewsets/
    """
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

    def retrieve(self, request, pk=None):
        """
        Override room retrieval to access by its unique_identifier,
        instead of its primary key (which is its running id.)
        """
        room = get_object_or_404(Room, unique_identifier=pk)
        serializer = self.get_serializer(room)
        return JsonResponse(serializer.data)

    def get_permissions(self):
        """
        Here we define the permissions required to access resources,
        depending on the action.
        For the room viewset, everything except for the list (get all)
        method would require the user to be authenticated.
        """
        if self.action == 'list':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
