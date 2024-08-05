from fastapi import APIRouter
from pyarr import RadarrAPI

import schemas.settings as settings
from utils.config_manager import ConfigManager
from utils.customSonarApi import customSonarAPI
from utils.general_arr_actions import link_arr_to_media_server
from utils.media_server_interaction import MediaServerinteracter

# region Configuration and Setup
router = APIRouter(prefix="/mediaserver", tags=["Media server"])
config_manager = ConfigManager()
config = config_manager.get_config()


# endregion


@router.get("/info")
def get_info():
    config = config_manager.get_config()
    media_server = MediaServerinteracter(config.MEDIASERVER.media_server_type, config.MEDIASERVER.media_server_base_url,
                                         config.MEDIASERVER.media_server_api_key)
    users = media_server.get_users()

    return {
        "users": users,
    }


@router.get("/media-info")
def get_media_info():
    config = config_manager.get_config()
    media_server = MediaServerinteracter(config.MEDIASERVER.media_server_type, config.MEDIASERVER.media_server_base_url,
                                         config.MEDIASERVER.media_server_api_key)
    sonarr = customSonarAPI(config.SONARR.base_url, config.SONARR.api_key)
    radarr = RadarrAPI(config.RADARR.base_url, config.RADARR.api_key)
    series = sonarr.get_series()
    movies = radarr.get_movie()

    favorites = media_server.get_all_favorites()
    played = media_server.get_played()

    favorited_sonarr = list(set(
        arr_item['id'] for item in favorites['Series']
        if (arr_item := link_arr_to_media_server(item, series)) is not None
    ))
    played_sonarr = list(set(
        arr_item['id'] for item in played['Series']
        if (arr_item := link_arr_to_media_server(item, series)) is not None
    ))
    favorited_radarr = list(set(
        arr_item['id'] for item in favorites['Movies']
        if (arr_item := link_arr_to_media_server(item, movies)) is not None
    ))
    played_radarr = list(set(
        arr_item['id'] for item in played['Movies']
        if (arr_item := link_arr_to_media_server(item, movies)) is not None
    ))

    return {
        "series": {
            "favorited": favorited_sonarr,
            "played": played_sonarr
        },
        "movies": {
            "favorited": favorited_radarr,
            "played": played_radarr
        }
    }


@router.get("/settings", response_model=settings.MediaServerSettings, description="Get mediaserver settings")
def get_settings() -> settings.MediaServerSettings:
    config = config_manager.get_config()
    return config.MEDIASERVER


@router.post("/settings", description="Update Radarr settings")
def post_settings(settings: settings.MediaServerSettings):
    config = config_manager.get_config()
    config.MEDIASERVER = settings
    config_manager.save_config_file(config)

# @router.get("/dry", description="Get the results of a dry run")
# def get_dry_run() -> JSONResponse:
#     return JSONResponse(radarr_run(dry=True))
