import spotipy
from fastapi import APIRouter
from spotipy.oauth2 import SpotifyClientCredentials

from utils.config_manager import ConfigManager
from utils.log_manager import LoggingManager
from utils.media_server_interaction import MediaServerinteracter
from utils.validators import fuzzy_str_match

# TODO:
# - Add support for video playlists
# - Add write overview to playlist and make it locked with info about playlist and that it is a managed playlist


# region Configuration and Setup
config_manager = ConfigManager()
config = config_manager.get_config()
logging_manager = LoggingManager()
sptpy = None
media_server = MediaServerinteracter(config.MEDIASERVER.media_server_type, config.MEDIASERVER.media_server_base_url,
                                     config.MEDIASERVER.media_server_api_key)


# endregion


def get_playlist_tracks(playlist_id):
    playlist_tracks = []
    offset = 0

    while True:
        response = sptpy.playlist_items(playlist_id, offset=offset)
        items = response['items']
        playlist_tracks.extend(items)
        if len(playlist_tracks) == response['total']:
            break
        offset += len(items)

    playlist_tracks = [playlist_track for playlist_track in playlist_tracks if
                       not playlist_track['track'].get('episode', False)]

    return playlist_tracks


def process_playlist_tracks(playlist_tracks, media_server_tracks_by_title):
    matched_tracks = set()

    for playlist_track in playlist_tracks:
        track_name = playlist_track['track']['name']
        track_album = playlist_track['track']['album']['name']
        track_artists_set = {artist['name'] for artist in playlist_track['track']['artists']}

        # Check by title quickly
        potential_matches = media_server_tracks_by_title.get(track_name, [])

        # If not matched fuzzy match by title
        if not potential_matches:
            for key, value in media_server_tracks_by_title.items():
                if fuzzy_str_match(track_name, key):
                    potential_matches = value
                    break

        for media_server_track in potential_matches:
            # if song is in the album but artist does not match it is still most likely a match
            if fuzzy_str_match(track_album, media_server_track['album']) or \
                    any(fuzzy_str_match(artist, media_server_artist) for artist in track_artists_set for
                        media_server_artist in media_server_track['artists']):
                matched_tracks.add(media_server_track['id'])
                break

    return matched_tracks


def process_playlist_audio(existing_server_playlists, media_server_tracks_by_title, playlist):
    playlist_tracks = get_playlist_tracks(playlist['id'])
    track_ids = process_playlist_tracks(playlist_tracks, media_server_tracks_by_title)

    existing_playlist = None
    playlist_name = f"{playlist['name']} - arrTools"
    for playlist in existing_server_playlists:
        if playlist['title'] == playlist_name:
            existing_playlist = playlist
            break

    if existing_playlist:
        print(f"Found existing playlist {playlist_name}")
        playlist_id = existing_playlist['id']
        existing_entries = media_server.get_items_from_playlist(playlist_id)
        existing_entries_ids = [entry['PlaylistItemId'] for entry in existing_entries]
        if len(existing_entries_ids) > 0:
            media_server.remove_items_from_playlist(playlist_id, existing_entries_ids)
        media_server.add_items_to_playlist(playlist_id, track_ids)
    else:
        print(f"Creating new playlist {playlist_name}")
        media_server.create_playlist(playlist_name, track_ids, 'Audio')


def main():
    media_server_tracks = media_server.get_music_items()
    # Index media_server_tracks by track title and album for quicker lookup
    media_server_tracks_by_title = {}

    for track in media_server_tracks:
        title = track['title']
        if title not in media_server_tracks_by_title:
            media_server_tracks_by_title[title] = []
        media_server_tracks_by_title[title].append(track)

    existing_server_playlists = media_server.get_playlist_items()

    for playlist in config.SPOTIFY.playlists:
        if playlist['type'] == 'audio':
            process_playlist_audio(existing_server_playlists, media_server_tracks_by_title, playlist)
        elif playlist['type'] == 'video':
            raise NotImplementedError("Video playlists are not yet supported")


def run():
    global sptpy, config, media_server
    config = config_manager.get_config()
    auth_manager = SpotifyClientCredentials(client_id=config.SPOTIFY.client_id,
                                            client_secret=config.SPOTIFY.client_secret)
    sptpy = spotipy.Spotify(auth_manager=auth_manager)
    media_server = MediaServerinteracter(config.MEDIASERVER.media_server_type, config.MEDIASERVER.media_server_base_url,
                                         config.MEDIASERVER.media_server_api_key)

    main()


if __name__ == "__main__":
    run()
