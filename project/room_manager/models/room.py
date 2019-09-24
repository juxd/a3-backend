from enum import Enum
from django.db import models
from .timestampable import Timestampable
from .user_suggestion import UserSuggestion
from rest_framework import serializers
import uuid

class Room(Timestampable):
    def generate_id():
        return str(uuid.uuid4())[:5]


    unique_identifier = models.CharField(max_length=5, unique=True,
                                         default=generate_id)
    location_latitude = models.DecimalField(max_digits=8, decimal_places=5, null=True)
    location_longitude = models.DecimalField(max_digits=8, decimal_places=5, null=True)
    name = models.CharField(max_length=30, null=False)

    class Meta:
        app_label = 'room_manager'
        db_table = 'room'

    @classmethod
    def exists(cls, room_id):
        return cls.objects.filter(unique_identifier=room_id).count() == 1


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['name', 'unique_identifier', 'location_latitude', 'location_longitude']
        read_only_fields = ['unique_identifier']


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
