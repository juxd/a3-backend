from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from rest_framework_simplejwt.tokens import AccessToken, UntypedToken, TokenError
from urllib import parse
import json

from .room import Room

from .models.room import Room as RoomModel

DEBUG = False

# TODO: Cache this with redis
# {room_id: <Room Object>}
rooms = {}


class PlaybackConsumer(WebsocketConsumer):
    def connect(self):
        self.is_valid = False
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = 'room_%s' % self.room_id

        # 1. Verify that room exists. If yes, get or create in-memory room
        if self.room_id not in rooms:
            if RoomModel.exists(self.room_id):
                rooms[self.room_id] = Room(self.room_id, self.room_group_name,
                                        rooms)
            else:
                self.close(404)
                return

        self.room = rooms[self.room_id]
        
        # 2. Verify JWT token and get user identity
        query_string = self.scope['query_string'].decode("utf-8")
        access_token = parse.parse_qs(query_string)['access_token'][0]

        try:
            self.user_id = AccessToken(access_token).get('user_id')
        except TokenError as e:
            print(e)
            self.close(401)
            return

        # 3. Add user to room and broadcast to channel layer
        self.room.add_user(self)
        async_to_sync(self.channel_layer.group_add)(self.room_group_name,
                                                    self.channel_name)
        
        # 4. Accept connection and send initial data
        self.is_valid = True
        self.accept()
        self.send_initial_data()

    def disconnect(self, close_code):
        if not self.is_valid:
            return

        self.room.remove_user(self)

        # TODO: Should we destroy room the moment there are no users?
        # if (self.room.is_empty()):
        #     rooms.pop(self.room_id)

        # Leave room channel layer
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name,
                                                        self.channel_name)

    def receive(self, text_data):
        data = json.loads(text_data)
        type = data['type']
        payload = data['payload']

        ### HANDLING OF CLIENT EVENTS ###
        # 1. Queue Event: Add songs into room's queue
        if type == 'queueEvent':
            added = self.room.add_songs(payload['songs'])

            # Skip sending broadcast if no songs were added to queue
            if added == []: return

            data['payload']['songs'] = added

        # 2. Vote Action Event: Tally votes in room
        elif type == 'voteActionEvent':
            self.room.vote_songs(self, payload['votes'])

            # Convert to vote count event
            songs = []
            for vote in payload['votes']:
                id = vote['id']
                song = {'id': id, 'votes': self.room.get_vote_count(id)}
                songs.append(song)
            data = {'type': 'voteCountEvent', 'payload': {'songs': songs}}

        # Propagate message to room channel layer
        async_to_sync(self.channel_layer.group_send)(self.room_group_name,
                                                     data)

    ### HANDLING OF CHANNEL LAYER EVENTS ###
    # 1. Queue Event: Notify clients of new queue songs
    def queueEvent(self, json_data):
        self.send(text_data=json.dumps(json_data))

    # 2. Playback Event: Notify clients of new now playing song
    def playbackEvent(self, json_data):
        self.send(text_data=json.dumps(json_data))

    # 3. Vote Event: Notify clients of new vote counts
    def voteCountEvent(self, json_data):
        self.send(text_data=json.dumps(json_data))

    ### HELPER FUNCTIONS ###

    def send_initial_data(self):
        self.send_queue()
        self.send_user_votes()
        self.send_now_playing()

    # Send all songs to a client
    def send_queue(self):
        data = {
            'type': 'queueEvent',
            'payload': {
                'songs': self.room.get_queue()
            }
        }

        self.send(text_data=json.dumps(data))

    # Send a user's previous votes
    def send_user_votes(self):
        data = {
            'type': 'voteActionEvent',
            'payload': self.room.get_user_votes(self.user_id)
        }
        self.send(text_data=json.dumps(data))

    # Send the current playing song in the room
    def send_now_playing(self):
        if self.room.has_now_playing():
            data = {
                'type': 'playbackEvent',
                'payload': self.room.get_now_playing()
            }
        else:
            data = {'type': 'playbackEvent', 'payload': {}}

        self.send(text_data=json.dumps(data))

    def __str__(self):
        return "User: (ID %s, Room ID %s)" % (self.user_id, self.room_id)
