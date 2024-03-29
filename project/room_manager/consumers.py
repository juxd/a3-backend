from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from rest_framework_simplejwt.tokens import AccessToken, UntypedToken, TokenError
from urllib import parse
import json
import logging

from .room import Room
from .models.room import Room as RoomModel

# {room_id: <Room Object>}
ROOMS = {}

class PlaybackConsumer(WebsocketConsumer):
    def connect(self):
        self.is_valid = False
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = 'room_%s' % self.room_id

        # 1. Verify that room exists. If yes, get or create in-memory room
        if self.room_id not in ROOMS:
            self.owner_id = RoomModel.get_owner_id_if_exists(self.room_id)
            if self.owner_id is not None:
                ROOMS[self.room_id] = Room(self.room_id, self.room_group_name, self.owner_id)
            else:
                logging.error("Room model for " + str(self.room_id) +
                              " not found in DB")
                self.close(404)
                return

        logging.debug("In-memory Room with " + str(self.room_id) + " found")

        self.room = ROOMS[self.room_id]

        # 2. Verify JWT token and get user identity
        query_string = self.scope['query_string'].decode("utf-8")
        access_token = parse.parse_qs(query_string)['access_token'][0]

        try:
            self.user_id = AccessToken(access_token).get('user_id')
        except TokenError as e:
            logging.error(e)
            self.close(401)
            return
        
        logging.debug("User identified")

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

        # Leave room channel layer
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name,
                                                        self.channel_name)

    def receive(self, text_data):
        data = json.loads(text_data)
        type = data['type']
        payload = data['payload']

        ### HANDLING OF CLIENT EVENTS ###
        # 0. Ping
        if type == 'ping':
            return self.pong()
        
        # 1. Queue Event: Add songs into room's queue
        elif type == 'queueEvent':
            added = self.room.add_songs(payload['songs'])

            # Skip sending broadcast if no songs were added to queue
            if added == []: return

            data['payload']['songs'] = added
            data['payload']['type'] = 'changes'

        # 2. Vote Action Event: Tally votes in room
        elif type == 'voteActionEvent':
            valid_votes = self.room.vote_songs(self, payload['votes'])

            # Confirm votes accepted
            self.send_user_votes(valid_votes)

            # Convert to vote count event to inform room
            songs = []
            for vote in valid_votes:
                id = vote['id']
                song = {'id': id, 'votes': self.room.get_vote_count(id)}
                songs.append(song)
            data = {'type': 'voteCountEvent', 'payload': {'songs': songs}}
        
        elif type == 'stopEvent':
            pass

        else:
            return

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

    # 4. Stop Event: Notify clients of a stop in playback
    def stopEvent(self, json_data):
        self.send(text_data=json.dumps(json_data))

    ### HELPER FUNCTIONS ###

    def pong(self):
        data = {
            'type': 'pong',
            'payload': {}
        }
        self.send(text_data=json.dumps(data))

    def send_initial_data(self):
        self.send_queue()
        self.send_all_user_votes()
        self.send_now_playing()

    # Send all songs to a client
    def send_queue(self):
        data = {
            'type': 'queueEvent',
            'payload': {
                'songs': self.room.get_queue(),
                'type': 'all'
            }
        }
        self.send(text_data=json.dumps(data))

    # Send a user's previous votes
    def send_all_user_votes(self):
        data = {
            'type': 'voteActionEvent',
            'payload': { 'votes' : self.room.get_user_votes(self.user_id) }
        }
        self.send(text_data=json.dumps(data))

    # Confirm a user's vote by sending it back
    def send_user_votes(self, votes):
        data = {
            'type': 'voteActionEvent',
            'payload': { 'votes' : votes }
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
