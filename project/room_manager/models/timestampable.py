from django.db import models


class Timestampable(models.Model):
    """
    Base abstract class that would timestamp models on creation.
    By default, each class that extends this would:
    - timestamp the `created_at` field on creation
    - timestamp the `updated_at` field on update
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
