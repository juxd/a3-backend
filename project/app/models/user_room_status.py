from django.db import models
from timestampable import Timestampable
from user import User
from room import Room

class UserRoomStatus(Timestampable):
    user = models.ForeignKey(User)
    room = models.ForeignKey(Room)

    class RoomStatuses(models.IntegerChoices):
        DISCONNECTED = 0
        CONNECTED = 1
        IDLE = 2

    status = models.IntegerField(choices=RoomStatuses)

    class Meta:
        app_name = 'app'
        table_name = 'user_room'
