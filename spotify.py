import re

import spotipy as spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from backend import spotify_id, spotify_secret

# Replace with your own Spotify API credentials
client_id = spotify_id
client_secret = spotify_secret

# Authenticate with Spotify API
client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Replace with your Spotify playlist share link


def is_valid_url(playlist_url):
    pattern = r"^https://open.spotify.com/playlist/[\w\d]+(\?.*)?$"
    match = re.match(pattern, playlist_url)
    return bool(match)


def get_playlist(playlist_url):
    try:
        playlist_id = playlist_url.split("/")[-1].split("?")[0]
        return sp.playlist(playlist_id), sp.playlist_tracks(playlist_id)["items"]
    except:
        return False
