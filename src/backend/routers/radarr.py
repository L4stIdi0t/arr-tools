import json
from fastapi import APIRouter, Body
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

test =  {"title":"Let Him Go","originalTitle":"Let Him Go","originalLanguage":{"id":1,"name":"English"},"alternateTitles":[{"sourceType":"tmdb","movieMetadataId":177,"title":"L'un des notres","id":8729},{"sourceType":"tmdb","movieMetadataId":177,"title":"Відпусти його","id":12787}],"secondaryYearSourceId":0,"sortTitle":"let him go","sizeOnDisk":4017177923,"status":"released","overview":"Following the loss of their son, a retired sheriff and his wife leave their Montana ranch to rescue their young grandson from the clutches of a dangerous family living off the grid in the Dakotas.","inCinemas":"2020-11-05T00:00:00Z","physicalRelease":"2021-02-02T00:00:00Z","digitalRelease":"2020-11-24T00:00:00Z","images":[{"coverType":"poster","url":"/MediaCover/283/poster.jpg?lastWrite=638401461206769962","remoteUrl":"https://image.tmdb.org/t/p/original/EsLZoT8oHhQlGd1QpdbnvnwTzO.jpg"},{"coverType":"fanart","url":"/MediaCover/283/fanart.jpg?lastWrite=638401461207239963","remoteUrl":"https://image.tmdb.org/t/p/original/ZLD4pjmMLt9I3t1a7SFJBekIh1.jpg"}],"website":"https://www.focusfeatures.com/let-him-go","year":2020,"youTubeTrailerId":"bE8pwEF-3TI","studio":"The Mazur Kaplan Company","path":"/data/media/movies/movies_hd/Let Him Go (2020) [tmdb-596161]","qualityProfileId":"WEB-HD","hasFile":True,"movieFileId":19452,"monitored":False,"minimumAvailability":"released","isAvailable":True,"folderName":"/data/media/movies/movies_hd/Let Him Go (2020) [tmdb-596161]","runtime":114,"cleanTitle":"lethimgo","imdbId":"tt9340860","tmdbId":596161,"titleSlug":"596161","rootFolderPath":"/data/media/movies/movies_hd/","genres":["Drama","Thriller","Crime"],"tags":["traktanticipated"],"added":"2020-09-17T18:09:14Z","ratings":{"imdb":{"votes":35323,"value":6.7,"type":"user"},"tmdb":{"votes":610,"value":6.816,"type":"user"},"metacritic":{"votes":0,"value":63,"type":"user"},"rottenTomatoes":{"votes":0,"value":85,"type":"user"}},"movieFile":{"movieId":283,"relativePath":"Let Him Go (2020) [tmdb-596161] - [WEBDL-1080p][AC3 5.1][x264]-EVO.mkv","path":"/data/media/movies/movies_hd/Let Him Go (2020) [tmdb-596161]/Let Him Go (2020) [tmdb-596161] - [WEBDL-1080p][AC3 5.1][x264]-EVO.mkv","size":4017177923,"dateAdded":"2024-01-06T13:55:20Z","releaseGroup":"EVO","edition":"","languages":[{"id":1,"name":"English"}],"quality":{"quality":{"id":3,"name":"WEBDL-1080p","source":"webdl","resolution":1080,"modifier":"none"},"revision":{"version":1,"real":0,"isRepack":False}},"customFormatScore":0,"indexerFlags":0,"mediaInfo":{"audioBitrate":384000,"audioChannels":5.1,"audioCodec":"AC3","audioLanguages":"eng","audioStreamCount":1,"videoBitDepth":8,"videoBitrate":0,"videoCodec":"x264","videoFps":23.976,"videoDynamicRange":"","videoDynamicRangeType":"","resolution":"1920x1080","runTime":"1:53:59","scanType":"Progressive","subtitles":""},"qualityCutoffNotMet":False,"id":19452},"popularity":46.339,"statistics":{"movieFileCount":1,"sizeOnDisk":4017177923,"releaseGroups":["EVO"]},"id":283}

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
    return radarr.get_movie()


@router.post("/item", description="Edit an item")
def edit_item(item: dict):
    return radarr.upd_movie(item)

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
