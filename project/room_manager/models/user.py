from datetime import datetime
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from typing import Dict, Tuple, Union
from .timestampable import Timestampable
from rest_framework import serializers


class User(Timestampable, AbstractBaseUser):
    display_name = models.CharField(max_length=40, null=False, blank=True)
    access_token = models.CharField(max_length=200, null=True, blank=True)
    refresh_token = models.CharField(max_length=200, null=True, blank=True)
    auth_code = models.CharField(max_length=200, null=True, blank=True)
    token_expires_in = models.PositiveIntegerField(null=True, blank=True)
    token_issue_time = models.DateTimeField(null=True, blank=True)
    identifier = models.CharField(max_length=40, unique=True)
    email = models.EmailField()
    device_id = models.CharField(max_length=200, null=True, blank=True)

    USERNAME_FIELD = 'identifier'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    @classmethod
    def find_or_create_user(cls, user_info: Dict[str, str],
                            token_data: Dict[str, Union[int, str]]
                            ) -> Tuple['User', bool]:
        #TODO: process info, like check existence, etc.
        user, created = cls.objects.get_or_create(identifier=user_info['id'])
        if created:
            user.display_name = user_info['display_name']
            user.email = user_info['email']
        user.access_token = token_data['access_token']
        user.refresh_token = token_data['refresh_token']
        user.token_issue_time = datetime.now()
        user.token_expires_in = token_data['expires_in']
        user.save()
        return user, created

    @classmethod
    def get_device_and_token(cls, user_ids):
        users = cls.objects.filter(identifier=user_ids)
        return list(users.values_list('identifier', 'access_token', 'device_id'))

    class Meta:
        app_label = 'room_manager'
        db_table = 'user'


class UserTokenDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        TOKEN_FIELDS = [
            'access_token', 'refresh_token', 'token_expires_in',
            'token_issue_time'
        ]
        read_only_fields = TOKEN_FIELDS
        fields = TOKEN_FIELDS
