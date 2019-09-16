from django.db import models
from timestampable import Timestampable
from user_suggestion import UserSuggestion

class Room(Timestampable):
    unique_identifier = models.CharField(max_length=30)
    location_latitude = models.DecimalField(max_digits=8, decimal_places=5)
    location_longitude = models.DecimalField(max_digits=8, decimal_places=5)

    class Meta:
        app_name = 'app'
        table_name = 'room'


class RoomQueuedSong(Timestampable):
    user_suggestion = models.OneToOne(
        UserSuggestion,
        on_delete=Models.CASCADE,
    )
    room = models.ForeignKey(Room)

    class TrackStatuses(models.IntegerChoices):
        NOT_IN_QUEUE = 0
        QUEUED = 1
        CURRENTLY_PLAYING = 2
        FINISHED_PLAYING = 3

    votes = models.IntegerField()
    order_in_queue = models.IntegerField()
    track_status = models.IntegerField(choices=TrackStatuses)

    class Meta:
        app_name = 'app'
        table_name = 'room_queue'
