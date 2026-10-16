from system_layer.spotify_controller import (
    play_song,
    pause_music,
    resume_music,
    next_song,
    previous_song,
    play_playlist,
    play_liked_songs,
    shuffle_on,
    shuffle_off,
    repeat_track,
    repeat_playlist,
    repeat_off,
    get_current_track_info,
    toggle_play_pause
)

skill = {
    "name": "Spotify",
    "priority": 40
}


def can_handle(command):
    command = command.lower()

    keywords = [
        "spotify",
        "play",
        "pause",
        "resume",
        "next",
        "previous",
        "shuffle",
        "repeat",
        "liked songs",
        "playlist",
        "music",
        "what song",
        "what is playing",
        "current song",
        "current track"
    ]

    return any(word in command for word in keywords)


def execute(command):
    command = command.lower()

    # Query current song
    if any(q in command for q in ["what song", "what is playing", "current song", "current track"]):
        info = get_current_track_info()
        if info and info.get("title"):
            state_str = "Playing" if info.get("playing") else "Paused"
            return f"Currently on Spotify: {info['title']} by {info['artist']} ({state_str}), Sir."
        return "No track is currently playing on Spotify, Sir."

    # Pause
    if "pause" in command:
        return pause_music()

    # Resume
    if "resume" in command or "continue" in command:
        return resume_music()

    # Next
    if "next" in command:
        return next_song()

    # Previous
    if "previous" in command or "back" in command:
        return previous_song()

    # Shuffle
    if "shuffle on" in command:
        return shuffle_on()

    if "shuffle off" in command:
        return shuffle_off()

    # Repeat
    if "repeat song" in command:
        return repeat_track()

    if "repeat playlist" in command:
        return repeat_playlist()

    if "repeat off" in command:
        return repeat_off()

    # Liked Songs
    if "liked songs" in command:
        return play_liked_songs()

    # Playlist
    if "playlist" in command:
        playlist = command.split("playlist", 1)[1].strip()

        if playlist:
            return play_playlist(playlist)

        return "Which playlist should I play?"

    # Play Song
    if "play" in command:
        song = command.replace("spotify", "")
        song = song.replace("play", "")
        song = song.strip()

        if song:
            return play_song(song)

        return "Which song should I play?"

    return None