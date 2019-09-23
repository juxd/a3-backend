"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from .room_manager.rest_endpoints import authorization
from .room_manager.rest_endpoints import user
from .room_manager.rest_endpoints import room

urlpatterns = [
    path('admin/', admin.site.urls),
    path('authorize/new/', authorization.initiate),
    path('authorize/done/', authorization.exchange_token),
    path('authorize/refresh/', authorization.refresh_token),
    path('user/device/', user.device),
    path('rooms/', room.create),
]
