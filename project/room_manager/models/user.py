from datetime import datetime
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from typing import Dict, Tuple, Type, Union
from .timestampable import Timestampable

class User(Timestampable, AbstractBaseUser):
    display_name = models.CharField(max_length=40, null=False, blank=True)
    access_token = models.CharField(max_length=200, null=True, blank=True)
    refresh_token = models.CharField(max_length=200, null=True, blank=True)
    auth_code = models.CharField(max_length=200, null=True, blank=True)
    token_validity = models.PositiveIntegerField(null=True, blank=True)
    token_issue_time = models.DateTimeField(null=True, blank=True)
    identifier = models.CharField(max_length=40, unique=True)
    email = models.EmailField()

    USERNAME_FIELD = 'identifier'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    @classmethod
    def find_or_create_user(cls,
                            user_info: Dict[str, str],
                            token_data: Dict[str, Union[int, str]]) -> Tuple['User', bool]:
        #TODO: process info, like check existence, etc.
        user, created = cls.get_or_create(identifier=user_info[id])
        if created:
            user.display_name = user_info['display_name']
            user.email = user_info['email']
        user.access_token = token_data['access_token']
        user.refresh_token = token_data['refresh_token']
        user.token_issue_time = datetime.now()
        user.token_validity = int(token_data['expires_in'])
        user.save()
        return user, created

    class Meta:
        app_label = 'room_manager'
        db_table = 'user'
