from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json

class PlaybackConsumer(WebsocketConsumer):
    
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'room_%s' % self.room_name

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()
        self.sendalltracks()

    def disconnect(self, close_code):

        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            text_data
        )

    # Handle content event
    def queue_event(self, text_data):

        # Send message to client
        self.send(text_data)

    # Handle join event
    def user_event(self, text_data):

        # Send message to client
        self.send(text_data)

    # Send all tracks to a client
    def sendalltracks(self):
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
