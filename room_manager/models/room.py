from enum import Enum
from django.db import models
from .timestampable import Timestampable
from .user_suggestion import UserSuggestion

class Room(Timestampable):
    unique_identifier = models.CharField(max_length=30)
    location_latitude = models.DecimalField(max_digits=8, decimal_places=5)
    location_longitude = models.DecimalField(max_digits=8, decimal_places=5)

    class Meta:
        app_label = 'app'
        db_table = 'room'


class RoomQueuedSong(Timestampable):
    user_suggestion = models.OneToOneField(UserSuggestion,on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    class TrackStatuses(Enum):
        NOT_IN_QUEUE = 0
        QUEUED = 1
        CURRENTLY_PLAYING = 2
        FINISHED_PLAYING = 3

    votes = models.IntegerField()
    order_in_queue = models.IntegerField()
    track_status = models.PositiveSmallIntegerField(choices=tuple([(s.value, s.name) for s in TrackStatuses]))

    class Meta:
        app_label = 'app'
        db_table = 'room_queue'
