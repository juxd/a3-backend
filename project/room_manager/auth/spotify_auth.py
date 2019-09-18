from django.conf import settings
from rest_framework.request import Request
from project.room_manager.models import User
from typing import Union
from . import spotify_api as api


class SpotifyBackend:
    def authenticate(self,
                     request: Request,
                     error: Union[str, None] = None,
                     code: Union[str, None] = None,
                     state: Union[str, None] = None) -> Union[User, None]:
        #TODO: check state for request validity
        if error:
            return None
        try:
            token_data = api.get_token(code)
            user_info = api.get_user_info(token_data)
            user, _ = User.find_or_create_user(user_info, token_data)
            return user
        except Exception as e:
            if settings.DEBUG:
                print(e)
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
