import json
from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi.responses import JSONResponse

import schemas.settings as settings
from database.database import program_db_dependency
from models.webSettings import SwipeArrSeenRadarr, SwipeArrSeenSonarr
from utils.config_manager import ConfigManager

# region Configuration and Setup
router = APIRouter(prefix="/system", tags=["system"])
config_manager = ConfigManager()


# endregion


@router.get("/health")
async def search_music():
    return JSONResponse({"message": "OK"})


@router.get("/changelog")
async def get_changelog():
    with open('./data/changelog.json') as f:
        return JSONResponse(json.loads(f.read()))


@router.get("/settings")
async def get_settings() -> settings.Config:
    config_manager.load_config_file()
    return config_manager.get_config()


@router.get("/user-settings")
async def get_user_settings():
    try:
        with open('./data/user-config.json', 'r', encoding='utf-8') as userFile:
            return json.loads(userFile.read())
    except FileNotFoundError:
        return


@router.put("/user-settings")
async def put_user_settings(settings: Annotated[str, Form()]):
    with open('./data/user-config.json', 'w', encoding='utf-8') as userFile:
        userFile.write(settings)


@router.get("/seen-items")
async def get_seen_items(db: program_db_dependency):
    return {
        "radarr": [item.itemId for item in db.query(SwipeArrSeenRadarr).all()],
        "sonarr": [item.itemId for item in db.query(SwipeArrSeenSonarr).all()]
    }


@router.post("/seen-item")
async def add_seen_item(db: program_db_dependency, id: Annotated[int, Form()], arr: Annotated[str, Form()]):
    db_model = None
    arr = arr.casefold()
    if arr == "radarr":
        db_model = SwipeArrSeenRadarr
    elif arr == "sonarr":
        db_model = SwipeArrSeenSonarr

    if not db_model:
        return

    new_item = db_model(
        itemId=id
    )
    db.add(new_item)
    db.commit()


@router.delete("/clear-seen-items")
async def clear_seen_items(db: program_db_dependency):
    db.delete(SwipeArrSeenSonarr)
    db.delete(SwipeArrSeenRadarr)
    db.commit()
