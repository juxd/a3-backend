from ..models import User
from ..models.user import UserDeviceSerializer
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.http import JsonResponse


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserDeviceSerializer

    @action(methods=['PUT', 'PATCH'],
            detail=False,
            permission_classes=[IsAuthenticated],
            url_path='device')
    def update_device(self, request, pk=None):
        user = request.user
        if user is None:
            return JsonResponse({'error': 'Unauthenticated!'},
                                status=status.HTTP_401_UNAUTHORIZED)
        serializer = UserDeviceSerializer(user, data=request.data)
        serializer.is_valid()
        serializer.save()
        if settings.DEBUG:
            print(request.data)
            print(serializer.data)
        return JsonResponse(serializer.data)
