from django.conf import settings
from asgiref.sync import async_to_sync
from enum import Enum
import heapq
import base64
import json
import threading
import time
import requests as pyrequests

from .models.user import User

DEBUG = False
VOTE_DIRECTION_UP = 'up'
VOTE_DIRECTION_DOWN = 'down'

class Room:
    def __init__(self, room_id, room_group_name, parent):

        if DEBUG: print("ROOM CREATED")

        self.room_id = room_id
        self.room_group_name = room_group_name
        self.user_consumers = []
        self.user_votes = {} # {user_id : {song_id, direction}}
        self.queue = []
        self.now_playing = None

    def add_user(self, consumer):

        if DEBUG: print("USER ADDED", self.user_consumers)

        self.user_consumers.append(consumer)
    
    def remove_user(self, consumer):
        
        self.user_consumers.remove(consumer)

    def is_empty(self):

        return len(self.user_consumers) == 0

    # Returns the list of songs added
    def add_songs(self, data):

        added_songs = []
        
        for song_json in data:
            room_queued_song = RoomQueuedSong.from_json(song_json)
            heapq.heappush(self.queue, room_queued_song)
            added_songs.append(room_queued_song)
        
        if self.now_playing is None: 
            song_played = self.advance_queue()
            added_songs = [song for song in added_songs if not song.id == song_played.id]
        
        return [song.to_json() for song in added_songs]
    
    def vote_songs(self, consumer, data):

        user_id = consumer.user_id

        if user_id not in self.user_votes: self.user_votes[user_id] = {}
        existing_votes = self.user_votes[user_id]

        for new_vote in data:
            song_id = new_vote['id']
            song = self.get_song(song_id)
            
            new_vote_direction = new_vote['voteDirection']

            # User voted on song before
            if song_id in existing_votes:
                existing_vote_direction = existing_votes.pop(song_id)
                song.undo_vote(existing_vote_direction)
                if new_vote_direction != existing_vote_direction:
                    existing_votes[song_id] = new_vote_direction
                    song.do_vote(new_vote_direction)
            
            # User has not voted on song before
            else:
                existing_votes[song_id] = new_vote_direction
                song.do_vote(new_vote_direction)
            
            heapq.heapify(self.queue)
    
    # Returns the song played
    def advance_queue(self):

        song_played = None

        if self.queue == []:
            self.now_playing = None
            json_data = {
                'type' : 'playbackEvent',
                'payload': {}
            }

        else: 
            song_played = heapq.heappop(self.queue)

            self.now_playing = song_played

            # TODO: Async the following
            # 1. Send request to Spotify to play track
            Room.play_song_for_users(song_played, self.user_consumers)

            # 2. Schedule function to execute when song ends
            thread = threading.Timer(song_played.duration/1000 - 1, self.advance_queue)
            thread.daemon = False
            thread.start()

            json_data = {
                'type' : 'playbackEvent',
                'payload': self.now_playing.to_json()
            }
        
        # 3. Broadcast song change to channel layer
        if len(self.user_consumers) > 0:
            channel_layer = self.user_consumers[0].channel_layer

            async_to_sync(channel_layer.group_send)(
                self.room_group_name,
                json_data
            )

        return song_played

    def get_song(self, song_id):

        for song in self.queue:
            if song.id  == song_id: return song
        
        raise RuntimeError("No song with " + str(song_id) + " in queue")

    def get_vote_count(self, song_id):

        for song in self.queue:
            if song.id == song_id: return song.votes
        return -1

    def get_queue(self):

        data = []
        for room_queued_song in self.queue: data.append(room_queued_song.to_json())
        return data

    def get_now_playing(self):

        return self.now_playing.to_json()

    def has_now_playing(self):

        return self.now_playing is not None


    @classmethod
    def play_song_for_users(cls, song, user_consumers):

        user_ids = (consumer.user_id for consumer in user_consumers)
        token_device_pairs = User.get_device_and_token(user_ids)

        # TODO: Make this async
        for user_id, user_token, device_id in token_device_pairs:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + user_token,
            }

            params = (('device_id', device_id), )

            data = '{"uris":["spotify:track:' + song.id + '"]}'

            response = pyrequests.put(
                'https://api.spotify.com/v1/me/player/play',
                headers=headers,
                params=params,
                data=data)

            # TODO: Send message to frontend to reconnect device
            if response.status_code >= 400:
                print(response.text)
                # remove user from room
                user_consumers[:] = [
                    consumer for consumer in user_consumers
                    if consumer.user_id != user_id
                ]

    @classmethod
    def get_song_duration(cls, song_id):

        # TODO: Throw exception if room and id not set
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + Room.get_app_token(),
        }

        response = pyrequests.get('https://api.spotify.com/v1/tracks/' +
                                  song_id,
                                  headers=headers)

        if response.status_code >= 400:
            raise pyrequests.RequestException(
                'Request for Track Information Failed')

        json_data = json.loads(response.text)
        return json_data['duration_ms']

    # TODO: Flesh this out into a proper flow inside spotify_api
    #   - Schedule refresh rather than get new token everytime?
    @classmethod
    def get_app_token(cls):
        raw_credentials = '%s:%s' % (settings.CLIENT_ID,
                                     settings.CLIENT_SECRET)
        encoded_bytes = base64.b64encode(raw_credentials.encode('utf-8'))
        encoded_string = str(encoded_bytes, 'utf-8')

        headers = {
            'Authorization': 'Basic ' + encoded_string,
        }

        data = {'grant_type': 'client_credentials'}

        response = pyrequests.post('https://accounts.spotify.com/api/token',
                                   headers=headers,
                                   data=data)
        if response.status_code >= 400:
            raise pyrequests.RequestException('App Authorisation Failed')
        data = json.loads(response.text)
        return data['access_token']


class RoomQueuedSong:

    @classmethod
    def from_json(cls, json):
        return RoomQueuedSong(
            json['id'], 
            json['name'],
            json['artists'],
            json['album'],
            json['isExplicit'],
            json['imageSource'],
            json['trackDuration'],
            json.get('votes', 0))

    def to_json(self):
        json = {}
        json['id'] = self.id
        json['name'] = self.name
        json['artists'] = self.artists
        json['album'] = self.album
        json['isExplicit'] = self.is_explicit
        json['imageSource'] = self.image_source
        json['trackDuration'] = self.duration
        json['votes'] = self.votes
        return json

    def do_vote(self, vote_direction):
        if vote_direction == VOTE_DIRECTION_UP: self.votes += 1
        if vote_direction == VOTE_DIRECTION_DOWN: self.votes -= 1

    def undo_vote(self, vote_direction):
        if vote_direction == VOTE_DIRECTION_UP: self.do_vote(VOTE_DIRECTION_DOWN)
        if vote_direction == VOTE_DIRECTION_DOWN: self.do_vote(VOTE_DIRECTION_UP)

    def __init__(self, id, name, artists, album, is_explicit, image_source, duration, votes):
        self.id = id
        self.name = name
        self.artists = artists
        self.album = album
        self.is_explicit = is_explicit
        self.image_source = image_source
        self.votes = votes
        self.duration = duration

    # Inherent ordering by votes, then id
    def __lt__(self, other):
        if self.votes < other.votes: return True
        return self.id < other.id


# class VoteDirection(Enum):
#     UP = 'up'
#     DOWN = 'down'
