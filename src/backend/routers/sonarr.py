from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pyarr import SonarrAPI

import schemas.settings as settings
from utils.config_manager import ConfigManager
from workers.sonarr import delete_unmonitored_files
from workers.sonarr import run as sonarr_run

# region Configuration and Setup
router = APIRouter(prefix="/sonarr", tags=["Sonarr"])
config_manager = ConfigManager()
config = config_manager.get_config()
sonarr = SonarrAPI(config.SONARR.base_url, config.SONARR.api_key)

# endregion


@router.get("/info")
def get_info():
    quality_profiles = [{k: v for k, v in d.items() if k in ['name', 'id']} for d in sonarr.get_quality_profile()]
    tags = [{k: v for k, v in d.items() if k in ['label', 'id']} for d in sonarr.get_tag()]

    return {
        "quality_profiles": quality_profiles,
        "tags": tags
    }


@router.get("/items", description="Get all series from Sonarr")
def get_items():
    return sonarr.get_series()


@router.post("/item", description="Edit an item")
def edit_item(item: dict):
    return sonarr.upd_series(item)


@router.delete("/item", description="Delete an item")
def delete_item(
        id: int = Query(..., description="ID of the item to delete"),
        importListExclusion: bool = Query(True, description="Whether to add the item to import list exclusion"),
        deleteFiles: bool = Query(False, description="Whether to delete associated files")
):
    sonarr.del_series(id, delete_files=deleteFiles)

    return {"message": f"Item with ID {id} deleted successfully."}


@router.get("/settings", response_model=settings.SonarrSettings, description="Get Sonarr settings")
def get_settings() -> settings.SonarrSettings:
    config = config_manager.get_config()
    return config.SONARR


@router.post("/settings", description="Update Sonarr settings")
def post_settings(settings: settings.SonarrSettings):
    config = config_manager.get_config()
    config.SONARR = settings
    config_manager.save_config_file(config)


@router.get("/dry", description="Get the results of a dry run")
def get_dry_run() -> JSONResponse:
    return JSONResponse(sonarr_run(dry=True))


@router.get("/delete-unmonitored", description="Get the results of a dry run of deleting")
def get_dry_run_delete() -> JSONResponse:
    return JSONResponse(delete_unmonitored_files(dry=True))


@router.delete("/delete-unmonitored", description="Delete the unmonitored files WARNING, no cancel...")
def delete_unmonitored_files_call() -> JSONResponse:
    return JSONResponse(delete_unmonitored_files())
