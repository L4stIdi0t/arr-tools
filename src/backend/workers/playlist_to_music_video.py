import logging

from utils.config_manager import ConfigManager
from utils.log_manager import LoggingManager
from utils.media_server_interaction import MediaServerinteracter
from utils.music_video.main import download_music_video
from utils.validators import fuzzy_str_match

# TODO:
# - Add write overview to playlist and make it locked with info about playlist and that it is a managed playlist


# region Configuration and Setup
config_manager = ConfigManager()
config = config_manager.get_config()
logging_manager = LoggingManager()
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
    unmatched_tracks = []

    for playlist_track in playlist_tracks:
        track_name = playlist_track['Name']
        track_artists_set = playlist_track['Artists']

        # Check by title quickly
        potential_matches = media_server_tracks_by_title.get(track_name, [])

        # If not matched fuzzy match by title
        if not potential_matches:
            for key, value in media_server_tracks_by_title.items():
                if fuzzy_str_match(track_name, key):
                    potential_matches = value
                    break

        for media_server_track in potential_matches:
            if any(fuzzy_str_match(artist, media_server_artist) for artist in track_artists_set for
                   media_server_artist in media_server_track['Artists']):
                matched_tracks.add(media_server_track['id'])
                break

        unmatched_tracks.append(playlist_track)

    return matched_tracks, unmatched_tracks


def process_playlist_video(playlist_tracks, existing_server_playlists, media_server_tracks_by_title, playlist_name):
    track_ids, missing_tracks = process_playlist_tracks(playlist_tracks, media_server_tracks_by_title)

    existing_playlist = None
    playlist_name = f"MV - {playlist_name} - arrTools"
    for playlist in existing_server_playlists:
        if playlist['title'] == playlist_name:
            existing_playlist = playlist
            break

    if existing_playlist:
        logging_manager.log(f"Playlist {playlist_name} already exists", level=logging.DEBUG)
        playlist_id = existing_playlist['id']
        existing_entries = media_server.get_items_from_playlist(playlist_id)
        existing_entries_ids = [entry['PlaylistItemId'] for entry in existing_entries]
        if len(existing_entries_ids) > 0:
            media_server.remove_items_from_playlist(playlist_id, existing_entries_ids)
        media_server.add_items_to_playlist(playlist_id, track_ids)
    else:
        logging_manager.log(f"Creating new playlist {playlist_name}", level=logging.DEBUG)
        media_server.create_playlist(playlist_name, track_ids, 'Audio')

    for missing_track in missing_tracks:
        download_music_video(missing_track['Name'], missing_track['Artists'])


def index_tracks_by_title(media_server_tracks):
    media_server_tracks_by_title = {}
    for track in media_server_tracks:
        title = track['title']
        if title not in media_server_tracks_by_title:
            media_server_tracks_by_title[title] = []
        media_server_tracks_by_title[title].append(track)
    return media_server_tracks_by_title


def main():
    media_server_video_tracks_by_title = index_tracks_by_title(media_server.get_music_video_items())

    existing_server_playlists = media_server.get_playlist_items()
    existing_server_playlists_by_id = {playlist['id']: playlist['title'] for playlist in existing_server_playlists}

    for playlist_id in config.MUSICVIDEO.convert_playlists:
        playlist_tracks = media_server.get_items_from_playlist(playlist_id)
        playlist_name = existing_server_playlists_by_id.get(playlist_id, None)
        if not playlist_name:
            continue

        process_playlist_video(playlist_tracks, existing_server_playlists, media_server_video_tracks_by_title,
                               playlist_name)


def run():
    global sptpy, config, media_server
    config = config_manager.get_config()
    media_server = MediaServerinteracter(config.MEDIASERVER.media_server_type, config.MEDIASERVER.media_server_base_url,
                                         config.MEDIASERVER.media_server_api_key)

    main()
