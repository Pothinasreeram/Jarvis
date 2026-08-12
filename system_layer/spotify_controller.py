import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

scope = (
    "user-read-playback-state "
    "user-modify-playback-state "
    "user-read-currently-playing "
    "playlist-read-private "
    "playlist-read-collaborative "
    "user-library-read"
)

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=scope,
        open_browser=True
    )
)


def play_song(song):
    results = sp.search(q=song, type="track", limit=10)

    items = results["tracks"]["items"]

    if not items:
        return "I couldn't find that song."

    uri = items[0]["uri"]

    devices = sp.devices()["devices"]

    if not devices:
        return "No Spotify device is active. Please open Spotify."

    device_id = devices[0]["id"]

    sp.start_playback(device_id=device_id, uris=[uri])

    return f"Playing {items[0]['name']} by {items[0]['artists'][0]['name']}"


def pause_music():
    sp.pause_playback()
    return "Music paused."


def resume_music():
    sp.start_playback()
    return "Resuming music."


def next_song():
    sp.next_track()
    return "Skipping to next song."


def previous_song():
    sp.previous_track()
    return "Playing previous song."

#Play a playlist by name

def play_playlist(name):
    playlists = sp.current_user_playlists(limit=50)

    for playlist in playlists["items"]:
        if playlist["name"].lower() == name.lower():

            devices = sp.devices()["devices"]

            if not devices:
                return "No Spotify device is active."

            device_id = devices[0]["id"]

            sp.start_playback(
                device_id=device_id,
                context_uri=playlist["uri"]
            )

            return f"Playing playlist {playlist['name']}"

    return "I couldn't find that playlist."

#Play liked songs

def play_liked_songs():

    devices = sp.devices()["devices"]

    if not devices:
        return "No Spotify device is active."

    device_id = devices[0]["id"]

    results = sp.current_user_saved_tracks(limit=50)

    uris = [track["track"]["uri"] for track in results["items"]]

    if not uris:
        return "Your liked songs are empty."

    sp.start_playback(
        device_id=device_id,
        uris=uris
    )

    return "Playing your liked songs."

 #Shuffle controls

def shuffle_on():

    sp.shuffle(True)

    return "Shuffle enabled."

def shuffle_off():

    sp.shuffle(False)

    return "Shuffle disabled."

#Repeat controls the playback of a track or a playlist.

def repeat_track():

    sp.repeat("track")

    return "Repeating current song."

def repeat_playlist():

    sp.repeat("context")

    return "Repeating playlist."

def repeat_off():

    sp.repeat("off")

    return "Repeat turned off."