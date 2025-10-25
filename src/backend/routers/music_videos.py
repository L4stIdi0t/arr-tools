import logging

from fastapi import APIRouter, Query
from fastapi import HTTPException

import schemas.settings as settings
from utils.config_manager import ConfigManager
from utils.log_manager import LoggingManager

# region Configuration and Setup
router = APIRouter(prefix="/music-video", tags=["Music video"])
config_manager = ConfigManager()
config = config_manager.get_config()
logging_manager = LoggingManager()


# endregion


@router.get(
    "/settings",
    response_model=settings.MusicVideoSettings,
    description="Get Music video settings",
)
def get_settings() -> settings.MusicVideoSettings:
    config = config_manager.get_config()
    return config.MUSICVIDEO


@router.post("/settings", description="Update Music video settings")
def post_settings(settings: settings.MusicVideoSettings):
    logging_manager.log("Updating Music video settings", level=logging.DEBUG)
    config = config_manager.get_config()
    config.MUSICVIDEO = settings
    config_manager.save_config_file(config)

    return HTTPException(status_code=200, detail="Music video settings updated")


@router.get("/playlists", description="Get all playlists for conversion")
def get_playlists():
    config = config_manager.get_config()
    return config.MUSICVIDEO.convert_playlists


@router.put("/playlist", description="Add a playlist for conversion")
def put_playlist(
    playlist_id: str = Query(..., description="ID of playlist"),
):
    """
    Add a playlist for conversion.

    Args:
        playlist_id (str): ID of playlist.

    Raises:
        HTTPException: If the playlist already exists
    """
    config = config_manager.get_config()

    if playlist_id not in config.MUSICVIDEO.convert_playlists:
        config.MUSICVIDEO.convert_playlists.append(playlist_id)
        config_manager.save_config_file(config)

        return HTTPException(status_code=200, detail=f"Playlist added {playlist_id}")
    else:
        raise HTTPException(
            status_code=400, detail=f"Playlist already exists {playlist_id}"
        )


@router.delete("/playlist", description="Delete a playlist from the conversion list")
def delete_playlist(playlist_id: str):
    config = config_manager.get_config()

    if playlist_id in config.MUSICVIDEO.convert_playlists:
        config.MUSICVIDEO.convert_playlists.remove(playlist_id)
        config_manager.save_config_file(config)
        return HTTPException(status_code=200, detail=f"Playlist deleted {playlist_id}")

    raise HTTPException(status_code=400, detail=f"Playlist not found {playlist_id}")
