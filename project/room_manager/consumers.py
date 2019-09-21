from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json

from .room import Room

# TODO: Cache this with redis
# {room_id: <Room Object>}
rooms = {}

class PlaybackConsumer(WebsocketConsumer):
    
    # Handle connection request from client
    def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = 'room_%s' % self.room_id

        # TODO: Extract user id from initial request
        self.user_id = '123'

        # TODO: Room creation should be triggered by POST
        if self.room_id not in rooms:
            rooms[self.room_id] = Room(self.room_id, 
                    self.room_group_name, 
                    rooms)
        self.room = rooms[self.room_id]

        # Add user to room
        self.room.add_user(self)

        # Add user to room channel layer
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        for consumer in self.room.user_consumers:
            print(consumer.user_id)

        self.accept()
        self.send_all_tracks()

    def disconnect(self, close_code):
        
        self.room.remove_user(self)

        # TODO: Should we destroy room the moment there are no users?
        if (self.room.is_empty):
            rooms.pop(self.room_id)

        # Leave room channel layer
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from client device
    def receive(self, text_data):

        data = json.loads(text_data)
        type = data['type']
        message = data['message']
        if (type == 'queue_event'):
            song = self.room.has_song(message['id'])
            if (song is not None): song.votes = message['votes']
            else: self.room.add_track(message)

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            text_data
        )

    # Handle content event
    def queue_event(self, text_data):

        # Send message to client
        self.send(text_data)

    # Handle playback event
    def playback_event(self, text_data):

        # Send message to client
        self.send(text_data)


    # Send all tracks to a client
    def send_all_tracks(self):
        # TODO: Send existing list of tracks instead of sample track

        self.send(text_data=json.dumps({
            "type":"queue_event",
            "message": { "id": "123", 
            "name" : "Name", 
            "artists" : "Artist", 
            "album" : "Album", 
            "isExplicit" : "false", 
            "imageSource" : "www.example.com",
            "votes":9 }
        }))

