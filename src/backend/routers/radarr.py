from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pyarr import RadarrAPI

import schemas.settings as settings
from utils.config_manager import ConfigManager
from workers.radarr import delete_unmonitored_files
from workers.radarr import run as radarr_run

# region Configuration and Setup
router = APIRouter(prefix="/radarr", tags=["Radarr"])
config_manager = ConfigManager()
config = config_manager.get_config()
radarr = RadarrAPI(config.RADARR.base_url, config.RADARR.api_key)

# endregion


radarr_keys = [
    "title",
    "sortTitle",
    "status",
    "overview",
    "inCinemas",
    "physicalRelease",
    "digitalRelease",
    "images",
    "website",
    "year",
    "youTubeTrailerId",
    "qualityProfileId",
    "hasFile",
    "monitored",
    "runtime",
    "imdbId",
    "tmdbId",
    "tvdbId",
    "ratings",
    "popularity",
    "genres",
    "tags",
    "genres",
    "added",
    "statistics",
    "id"
]


@router.get("/info")
def get_info():
    quality_profiles = [{k: v for k, v in d.items() if k in ['name', 'id']} for d in radarr.get_quality_profile()]
    tags = [{k: v for k, v in d.items() if k in ['label', 'id']} for d in radarr.get_tag()]

    return {
        "quality_profiles": quality_profiles,
        "tags": tags
    }


@router.get("/items", description="Get all movies from Radarr")
def get_items():
    return [{k: v for k, v in d.items() if k in radarr_keys} for d in radarr.get_movie()]


@router.delete("/item", description="Delete an item")
def delete_item(
        id: int = Query(..., description="ID of the item to delete"),
        importListExclusion: bool = Query(True, description="Whether to add the item to import list exclusion"),
        deleteFiles: bool = Query(False, description="Whether to delete associated files")
):
    radarr.del_movie(id, delete_files=deleteFiles, add_exclusion=importListExclusion)

    return {"message": f"Item with ID {id} deleted successfully."}


@router.get("/settings", response_model=settings.RadarrSettings, description="Get Radarr settings")
def get_settings() -> settings.RadarrSettings:
    config = config_manager.get_config()
    return config.RADARR


@router.post("/settings", description="Update Radarr settings")
def post_settings(settings: settings.RadarrSettings):
    config = config_manager.get_config()
    config.RADARR = settings
    config_manager.save_config_file(config)


@router.get("/dry", description="Get the results of a dry run")
def get_dry_run() -> JSONResponse:
    return JSONResponse(radarr_run(dry=True))


@router.get("/delete-unmonitored", description="Get the results of a dry run of deleting")
def get_dry_run_delete() -> JSONResponse:
    return JSONResponse(delete_unmonitored_files(dry=True))


@router.delete("/delete-unmonitored", description="Delete the unmonitored files WARNING, no cancel...")
def delete_unmonitored_files_call() -> JSONResponse:
    return JSONResponse(delete_unmonitored_files())
