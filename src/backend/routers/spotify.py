import logging
import re

import spotipy
from fastapi import APIRouter, Query
from fastapi import HTTPException
from spotipy.oauth2 import SpotifyClientCredentials

import schemas.settings as settings
from utils.config_manager import ConfigManager
from utils.log_manager import LoggingManager

# region Configuration and Setup
router = APIRouter(prefix="/spotify", tags=["Spotify"])
config_manager = ConfigManager()
config = config_manager.get_config()
logging_manager = LoggingManager()


# endregion


@router.get(
    "/settings",
    response_model=settings.SpotifySettings,
    description="Get Spotify settings",
)
def get_settings() -> settings.SpotifySettings:
    config = config_manager.get_config()
    return config.SPOTIFY


@router.post("/settings", description="Update Spotify settings")
def post_settings(settings: settings.SpotifySettings):
    logging_manager.log("Updating Spotify settings", level=logging.DEBUG)
    config = config_manager.get_config()
    config.SPOTIFY = settings
    config_manager.save_config_file(config)

    return HTTPException(status_code=200, detail="Spotify settings updated")


@router.get("/playlists", description="Get all playlists for conversion")
def get_playlists():
    config = config_manager.get_config()
    return config.SPOTIFY.playlists


def get_playlist_id(playlist_url_id: str):
    pattern = r"\/playlist\/(\w+)"
    match = re.search(pattern, playlist_url_id)
    if match:
        playlist_id = match.group(1)
    else:
        playlist_id = playlist_url_id
    return playlist_id


@router.put("/playlist", description="Add a playlist for conversion")
def put_playlist(
    playlist_url_id: str = Query(..., description="Spotify playlist URL or ID"),
    playlist_type: str = Query(
        ..., description="Type of playlist: audio, video, or both"
    ),
):
    """
    Add a playlist for conversion.

    Args:
        playlist_url_id (str): Spotify playlist URL or ID.
        playlist_type (str): Type of playlist. Can be 'audio', 'video', or 'both'.

    Raises:
        HTTPException: If the playlist already exists or if there are issues with the
                       client ID/secret or finding the playlist.
    """

    config = config_manager.get_config()

    playlist_id = get_playlist_id(playlist_url_id)

    for playlist in config.SPOTIFY.playlists:
        if playlist["id"] == playlist_id:
            raise HTTPException(
                status_code=400,
                detail=f"Playlist already exists {playlist['name']}, ID: {playlist_id}",
            )

    try:
        auth_manager = SpotifyClientCredentials(
            client_id=config.SPOTIFY.client_id,
            client_secret=config.SPOTIFY.client_secret,
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
    except:
        raise HTTPException(
            status_code=400, detail="Client ID and/or secret are incorrect"
        )

    try:
        playlist_name = sp.playlist(playlist_id)["name"]
    except:
        raise HTTPException(
            status_code=400, detail="Can not find playlist, is it a private playlist?"
        )

    config.SPOTIFY.playlists.append(
        {"id": playlist_id, "type": playlist_type, "name": playlist_name}
    )
    config_manager.save_config_file(config)

    return HTTPException(
        status_code=200, detail=f"Playlist added {playlist_name}, ID: {playlist_id}"
    )


@router.delete("/playlist", description="Delete a playlist from the conversion list")
def delete_playlist(playlist_url_id: str):
    config = config_manager.get_config()

    playlist_id = get_playlist_id(playlist_url_id)

    for playlist in config.SPOTIFY.playlists:
        if playlist["id"] == playlist_id:
            config.SPOTIFY.playlists.remove(playlist)
            config_manager.save_config_file(config)
            return HTTPException(
                status_code=200,
                detail=f"Playlist deleted {playlist['name']}, ID: {playlist_id}",
            )

    raise HTTPException(status_code=400, detail=f"Playlist not found {playlist_id}")
