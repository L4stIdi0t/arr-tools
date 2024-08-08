import logging
import os
import shutil
import time

import requests
import yt_dlp
from sqlalchemy.orm import Session

from database.database import get_program_db
from models.media import musicVideoCache
from utils.config_manager import ConfigManager
from utils.log_manager import LoggingManager
from utils.music_video.imvdb_api import imvdb_search
from utils.music_video.shazam_api import shazam_cdn_search
from utils.music_video.shazam_api import shazam_confirm_song
from utils.parsers import make_filename_safe

# region Configuration and Setup
config_manager = ConfigManager()
config = config_manager.get_config()
logging_manager = LoggingManager()
db: Session = next(get_program_db())


# endregion

def _check_cache(title: str, artists: list, album: str = None):
    existing_data = db.query(musicVideoCache).filter_by(title=title, artists=artists, album=album).first()
    if not existing_data:
        return None
    if not existing_data.youtubeId and existing_data.dateAdded + 2592000 > time.time():
        db.delete(existing_data)
        db.commit()
        return None
    return existing_data


os.makedirs("./temp/downloading", exist_ok=True)
shutil.rmtree("./temp/downloading", ignore_errors=True)  # Cleanup old downloads if any


def _download_music_video(youtube_id: str, title: str, artists: list, album: str = None):
    ydl_opts = {
        # download the best mp4 format
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        # download the best audio and video and then merge them
        # "format": "bv+ba/b",
        "outtmpl": f"./temp/downloading/{youtube_id}.%(ext)s",
        "no_warnings": True,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_id])

    correct_song = True
    if config.MUSICVIDEO.check_song_with_recognition:
        correct_song = shazam_confirm_song(f"./temp/downloading/{youtube_id}.mp4", title, artists, album)

    if not correct_song:
        return False

    # Download thumbnail from i.ytimg.com
    artist_safe = make_filename_safe(artists[0])
    title_safe = make_filename_safe(title)
    os.makedirs(f"./musicVideoOutput/{artist_safe}", exist_ok=True)
    thumbnail_url = f"https://i.ytimg.com/vi/{youtube_id}/maxresdefault.jpg"
    thumbnail_path = f"./musicVideoOutput/{artist_safe}/{title_safe}.jpg"
    response = requests.get(thumbnail_url)
    if response.status_code == 200:
        with open(thumbnail_path, "wb") as thumbnail_file:
            thumbnail_file.write(response.content)

    os.makedirs(f"./musicVideoOutput/{artist_safe}", exist_ok=True)
    shutil.move(f"./temp/downloading/{youtube_id}.mp4", f"./musicVideoOutput/{artist_safe}/{title_safe}.mp4")
    return True


def download_music_video(title: str, artists: list, album: str = None):
    mv_config = config.MUSICVIDEO

    if not mv_config.enabled:
        return False

    if os.path.exists(f"./musicVideoOutput/{make_filename_safe(artists[0])}/{make_filename_safe(title)}.jpg"):
        return True

    existing_data = _check_cache(title, artists, album)
    if existing_data:
        if existing_data.downloadError:
            return False
        try:
            if _download_music_video(existing_data.youtubeId, title, artists, album):
                existing_data.downloadError = 0
                db.commit()
                return True
            else:
                existing_data.downloadError = 1
                db.commit()
                return False
        except Exception as e:
            logging_manager.log(f"Error downloading music video: {e}", level=logging.ERROR)
            existing_data.downloadError = 1
            db.commit()
            return False

    if not mv_config.use_youtube_search and not mv_config.use_shazam_search and not mv_config.use_imvdb:
        raise NotImplementedError("No search method is enabled")

    youtube_id, additional_info = None, None
    if mv_config.use_imvdb:
        youtube_id, additional_info = imvdb_search(title=title, artists=artists, album=album)
    if youtube_id is None and mv_config.use_shazam_search:
        youtube_id = shazam_cdn_search(title=title, artists=artists)
    if youtube_id is None and mv_config.use_youtube_search:
        raise NotImplementedError("Youtube search is not yet implemented")

    db_addition = musicVideoCache(youtubeId=youtube_id, title=title, artists=artists, album=album,
                                  additionalInfo=additional_info,
                                  dateAdded=round(time.time()))

    if not youtube_id:
        db.add(db_addition)
        db.commit()
        return False

    try:
        if _download_music_video(youtube_id, title, artists, album):
            db_addition.downloadError = 0
            db.add(db_addition)
            db.commit()
            return True
        else:
            db_addition.downloadError = 1
            db.add(db_addition)
            db.commit()
            return False
    except Exception as e:
        logging_manager.log(f"Error downloading music video: {e}", level=logging.ERROR)
        db_addition.downloadError = 1
        db.add(db_addition)
        db.commit()
        return False

    db.add(db_addition)
    db.commit()
    return False
