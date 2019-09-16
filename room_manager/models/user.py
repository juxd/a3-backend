from django.db import models
from .timestampable import Timestampable

class User(Timestampable):
    display_name = models.CharField(max_length=40, null=False, blank=True)
    token = models.CharField(max_length=200, null=True, blank=True)
    auth_code = models.CharField(max_length=200, null=True, blank=True)
    token_validity = models.PositiveIntegerField(null=True, blank=True)
    token_issue_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'app'
        db_table = 'user'
