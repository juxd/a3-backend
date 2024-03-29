from django.conf import settings
from asgiref.sync import async_to_sync
from enum import Enum
import heapq
import base64
import json
import threading
import time
import requests as pyrequests
import logging

from .models.user import User
from .models.room import Room as RoomModel
from . import consumers
from .auth import spotify_api

VOTE_DIRECTION_UP = 'up'
VOTE_DIRECTION_DOWN = 'down'


class Room:
    def __init__(self, room_id, room_group_name, owner_id):
        self.room_id = room_id
        self.room_group_name = room_group_name
        self.owner_id = owner_id
        self.user_consumers = []
        self.user_votes = {}  # {user_id : {song_id:direction}}
        self.queue = SongHeap()
        self.now_playing = None

    def add_user(self, consumer):
        self.user_consumers.append(consumer)

    def remove_user(self, consumer):
        self.user_consumers.remove(consumer)
        if self.is_zombie(): 
            consumers.ROOMS.pop(self.room_id)

    def is_zombie(self):
        return (len(self.user_consumers) == 0 and 
                self.now_playing is None and
                self.queue.get_size() == 0)

    # Returns the list of songs added
    def add_songs(self, data):
        added_songs = []

        for song_json in data:
            room_queued_song = RoomQueuedSong.from_json(song_json)
            self.queue.push(room_queued_song)
            added_songs.append(room_queued_song)

        if self.now_playing is None:
            song_played = self.advance_queue()
            logging.debug("song played " + str(song_played.name))
            if song_played is not None:
                added_songs = [
                    song for song in added_songs
                    if not song.id == song_played.id
                ]

        return [song.to_json() for song in added_songs]

    def vote_songs(self, consumer, data):
        user_id = consumer.user_id

        if user_id not in self.user_votes: self.user_votes[user_id] = {}
        existing_votes = self.user_votes[user_id]

        valid_votes = []
        for new_vote in data:
            song_id = new_vote['id']
            song = self.get_song(song_id)

            # Ignore songs that no longer exists
            if song is None: 
                continue

            vote_direction = new_vote['voteDirection']

            # User voted on song before
            if song_id in existing_votes:
                existing_vote_direction = existing_votes.pop(song_id)
                song.undo_vote(existing_vote_direction)

                # If new vote is in the opposite direction
                if vote_direction != existing_vote_direction: 
                    existing_votes[song_id] = vote_direction
                    song.do_vote(vote_direction)
                
                # If new vote is an undo action
                else:
                    new_vote['voteDirection'] = 'neutral'
        
            # User has not voted on song before
            else:
                existing_votes[song_id] = vote_direction
                song.do_vote(vote_direction)
                
            valid_votes.append(new_vote)
            self.queue.update(song)
        
        return valid_votes

    # Returns the song played
    def advance_queue(self):

        song_played = None
        
        # Check if room is deleted
        if RoomModel.get_owner_id_if_exists(self.room_id) is None:
            consumers.ROOMS.pop(self.room_id)
            json_data = {
                'type': 'stopEvent',
                'payload': 'close'
            }
        
        elif self.queue.is_empty():
            self.now_playing = None
            json_data = {'type': 'playbackEvent', 'payload': {}}
            if self.is_zombie(): consumers.ROOMS.pop(self.room_id)

        else:
            song_played = self.queue.pop()
            self.now_playing = song_played

            # TODO: Async the following
            # 1. Send request to Spotify to play track
            Room.play_song_for_owner(song_played, self)

            # 2. Schedule function to execute when song ends
            thread = threading.Timer(song_played.duration / 1000 - 1,
                                     self.advance_queue)
            thread.daemon = False
            thread.start()

            json_data = {
                'type': 'playbackEvent',
                'payload': self.now_playing.to_json()
            }

        # 3. Broadcast song change to channel layer
        if len(self.user_consumers) > 0:
            channel_layer = self.user_consumers[0].channel_layer

            async_to_sync(channel_layer.group_send)(self.room_group_name,
                                                    json_data)

        # 4. Remove user votes for the newly played song
        if song_played is not None:
            for _, votes in self.user_votes.items():
                if song_played.id in votes: votes.pop(song_played.id)

        return song_played

    # Returns None when no such song
    def get_song(self, song_id):
        return self.queue.get_song_by_id(song_id)

    def get_queue(self):
        return [song.to_json() for song in self.queue.get_all_songs()]

    def get_vote_count(self, song_id):
        song = self.queue.get_song_by_id(song_id)
        if song is not None:
            return song.votes
        else:
            raise RuntimeError("No song with " + str(song_id) + " in queue")

    def get_user_votes(self, user_id):
        # Input shape: {user_id : {song_id: direction}}
        # Output shape: [{'id': song_id, 'voteDirection':direction}]
        if user_id not in self.user_votes:
            return []
        votes = [{
            'id': song_id,
            'voteDirection': direction
        } for song_id, direction in self.user_votes[user_id].items()]
        return votes

    def get_now_playing(self):
        return self.now_playing.to_json()

    def has_now_playing(self):
        return self.now_playing is not None

    @classmethod
    def play_song_for_owner(cls, song, room):
        # user_ids = [consumer.user_id for consumer in room.user_consumers]
        user_data = User.get_device_and_tokens([room.owner_id])
        print(user_data)

        # TODO: Make this async
        for user_id, access_token, refresh_token, device_id in user_data:

            logging.debug("Device ID: " + device_id)
            access_token = Room.refresh_access_token(access_token, refresh_token)

            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + access_token,
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
                logging.error(response.text)
                logging.error("User ID: " + str(user_id))
                logging.error("Access Token: " + str(access_token))
                logging.error("Refresh Token: " + str(refresh_token))
                logging.error("Device ID: " + str(device_id))
                json_data = {
                    'type': 'stopEvent',
                    'payload': 'disconnect'
                }
                if len(room.user_consumers) > 0:
                    channel_layer = room.user_consumers[0].channel_layer

                    async_to_sync(channel_layer.group_send)(room.room_group_name, json_data)

    @classmethod
    def refresh_access_token(cls, access_token, refresh_token):
        # Refresh user's token
        spotify_params = {}
        spotify_params['access_token'] = access_token
        spotify_params['refresh_token'] = refresh_token
        try:
            spotify_api.get_user_info(spotify_params)
            return access_token
        except pyrequests.RequestException:
            pass
        refresh_response = spotify_api.refresh_token_info(spotify_params)
        return refresh_response['access_token']

class RoomQueuedSong:
    @classmethod
    def from_json(cls, json):
        return RoomQueuedSong(json['id'], json['name'], json['artists'],
                              json['album'], json['isExplicit'],
                              json['imageSource'], json['trackDuration'],
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
        if vote_direction == VOTE_DIRECTION_UP:
            self.do_vote(VOTE_DIRECTION_DOWN)
        if vote_direction == VOTE_DIRECTION_DOWN:
            self.do_vote(VOTE_DIRECTION_UP)

    def __init__(self, id, name, artists, album, is_explicit, image_source,
                 duration, votes):
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


class SongHeap(object):
    def __init__(self):
        self.key = lambda song: (-song.votes)
        self._data = []

    def push(self, song):
        heapq.heappush(self._data, (self.key(song), song))

    def pop(self):
        return heapq.heappop(self._data)[1]

    def update(self, song):
        self._data = [(key, x) if x.id != song.id else (self.key(song), song)
                      for (key, x) in self._data]
        heapq.heapify(self._data)

    def is_empty(self):
        return len(self._data) == 0

    def get_song_by_id(self, song_id):
        for _, x in self._data:
            if x.id == song_id: return x
        return None

    def get_all_songs(self):
        return [x for (key, x) in self._data]

    def get_size(self):
        return len(self._data)
