from enum import Enum
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from .timestampable import Timestampable
from .user_suggestion import UserSuggestion
from rest_framework import serializers, permissions
from .user import User, UserShareableSerializer

import uuid


class Room(Timestampable):
    def generate_id():
        return str(uuid.uuid4())[:5]

    unique_identifier = models.CharField(max_length=5,
                                         unique=True,
                                         default=generate_id)
    location_latitude = models.DecimalField(max_digits=8,
                                            decimal_places=5,
                                            null=True)
    location_longitude = models.DecimalField(max_digits=8,
                                             decimal_places=5,
                                             null=True)
    name = models.CharField(max_length=30, null=False)
    description = models.CharField(max_length=280, null=True, blank=True)
    owner = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    alive = models.PositiveSmallIntegerField(choices=((0, 'DEAD'), (1,
                                                                    'ALIVE')),
                                             default=0)

    class Meta:
        app_label = 'room_manager'
        db_table = 'room'

    def kill(self):
        """
        "Kills" the room
        """
        self.alive = 0
        self.save()

    @classmethod
    def get_owner_id_if_exists(cls, room_id):
        try:
            room = cls.objects.filter(alive=1).get(unique_identifier=room_id)
            return room.owner.identifier
        except ObjectDoesNotExist:
            return None




@receiver(post_save, sender=Room)
def turn_on(sender, instance, created, **kwargs):
    if created:
        instance.alive = 1
        instance.save()


class RoomOwnerPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.owner == request.user


class RoomSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Room
        fields = [
            'name', 'unique_identifier', 'location_latitude',
            'location_longitude', 'alive', 'owner', 'description'
        ]
        read_only_fields = ['unique_identifier']
        depth = 1


class RoomQueuedSong(Timestampable):
    user_suggestion = models.OneToOneField(UserSuggestion,
                                           on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    class TrackStatuses(Enum):
        NOT_IN_QUEUE = 0
        QUEUED = 1
        CURRENTLY_PLAYING = 2
        FINISHED_PLAYING = 3

    votes = models.IntegerField()
    order_in_queue = models.IntegerField()
    track_status = models.PositiveSmallIntegerField(
        choices=tuple([(s.value, s.name) for s in TrackStatuses]))

    class Meta:
        app_label = 'room_manager'
        db_table = 'room_queue'
