from enum import Enum
from django.db import models
from .timestampable import Timestampable
from .user import User
from .room import Room

class UserRoomStatus(Timestampable):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    class RoomStatuses(Enum):
        DISCONNECTED = 0
        CONNECTED = 1
        IDLE = 2

    status = models.IntegerField(choices=tuple([(s.value, s.name) for s in RoomStatuses]))

    class Meta:
        app_label = 'room_manager'
        db_table = 'user_room'
