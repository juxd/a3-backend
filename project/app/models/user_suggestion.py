from django.db import models
from user import User
from timestampable import Timestampable

class UserSuggestion(Timestampable):
    track_id = models.CharField(max_length=100, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    class Meta:
        db_table = 'user_suggestion'
        app_label = 'app'
