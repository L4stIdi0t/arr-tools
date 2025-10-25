import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from routers import mediaserver
from routers import music_videos
from routers import radarr
from routers import sonarr
from routers import spotify
from routers import system
from utils.log_manager import LoggingManager
from workers.workers import WorkerManager

logging_manager = LoggingManager()
logging_manager.log("Program is starting", level=logging.INFO)

app = FastAPI()

app.include_router(radarr.router, prefix="/api")
app.include_router(sonarr.router, prefix="/api")
app.include_router(spotify.router, prefix="/api")
app.include_router(music_videos.router, prefix="/api")
app.include_router(mediaserver.router, prefix="/api")
app.include_router(system.router, prefix="/api")

os.makedirs("./static/assets", exist_ok=True)  # Fix if using empty pull
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
os.makedirs("./static/favicon", exist_ok=True)  # Fix if using empty pull
app.mount("/favicon", StaticFiles(directory="static/favicon"), name="favicon")


@app.get("/{path:path}")
async def read_index():
    return FileResponse("./static/index.html")


def main_start():
    manager = WorkerManager("./workers/config.yml")
    manager.start_workers()


if __name__ == "__main__":
    main_start()
    uvicorn.run(app, host="0.0.0.0", port=9000)
