import glob
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
from utils.music_video.music_video_detect import detect_movement
from utils.music_video.nfo_writer import create_nfo
from utils.music_video.shazam_api import shazam_cdn_search
from utils.music_video.shazam_api import shazam_confirm_song
from utils.parsers import make_filename_safe

# region Configuration and Setup
config_manager = ConfigManager()
config = config_manager.get_config()
logging_manager = LoggingManager()
db: Session = next(get_program_db())


# endregion


def _cleanup_files(base_path):
    directory, file_prefix = os.path.split(base_path)
    for filename in os.listdir(directory):
        if filename.startswith(file_prefix):
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Error: {e.filename} - {e.strerror}.")


def _check_cache(title: str, artists: list, album: str = None):
    existing_data = (
        db.query(musicVideoCache)
        .filter_by(title=title, artists=artists, album=album)
        .first()
    )
    if not existing_data:
        return None
    if not existing_data.youtubeId and existing_data.dateAdded + 2592000 > time.time():
        db.delete(existing_data)
        db.commit()
        return None
    return existing_data


os.makedirs("./temp/downloading", exist_ok=True)
shutil.rmtree("./temp/downloading", ignore_errors=True)  # Cleanup old downloads if any


def _download_music_video(
    youtube_id: str, title: str, artists: list, album: str = None
):
    ydl_opts = {
        # download the best mp4 format
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        # download the best audio and video and then merge them
        # "format": "bv+ba/b",
        "outtmpl": f"./temp/downloading/{youtube_id}.%(ext)s",
        "no_warnings": True,
        "write-thumbnail": True,
        "subtitlesformat": "srt",
        "subtitleslangs": config.MUSICVIDEO.subtitle_languages,
        "writesubtitles": config.MUSICVIDEO.download_subtitles,
        "writeautomaticsub": config.MUSICVIDEO.download_subtitles,
        "sponsorblock-mark": True,
        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        ],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_id])

    correct_song = True
    if config.MUSICVIDEO.check_song_with_recognition:
        correct_song = shazam_confirm_song(
            f"./temp/downloading/{youtube_id}.mp4", title, artists, album
        )

    if not correct_song:
        _cleanup_files(f"./temp/downloading/{youtube_id}")
        return False

    is_music_video = True
    if config.MUSICVIDEO.check_song_for_movement:
        is_music_video = detect_movement(f"./temp/downloading/{youtube_id}.mp4", 5, 10)

    if not is_music_video:
        _cleanup_files(f"./temp/downloading/{youtube_id}")
        return False

    artist_safe = make_filename_safe(artists[0])
    title_safe = make_filename_safe(title)
    os.makedirs(f"./musicVideoOutput/{artist_safe}", exist_ok=True)
    shutil.move(
        f"./temp/downloading/{youtube_id}.mp4",
        f"./musicVideoOutput/{artist_safe}/{title_safe}.mp4",
    )

    # region Download thumbnail from i.ytimg.com
    os.makedirs(f"./musicVideoOutput/{artist_safe}", exist_ok=True)
    thumbnail_urls = [
        f"https://i.ytimg.com/vi/{youtube_id}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{youtube_id}/hqdefault.jpg",
    ]
    thumbnail_path = f"./musicVideoOutput/{artist_safe}/{title_safe}.jpg"
    for url in thumbnail_urls:
        response = requests.get(url)
        if response.status_code == 200:
            with open(thumbnail_path, "wb") as thumbnail_file:
                thumbnail_file.write(response.content)
            break
    # endregion

    # region Move subtitles
    subtitle_formats = ["srt", "vtt", "ass", "ssa", "sub", "idx"]
    for fmt in subtitle_formats:
        srt_files = glob.glob(f"./temp/downloading/{youtube_id}*.{fmt}")
        for srt_file in srt_files:
            language_code = srt_file.split(f"{youtube_id}.")[-1]
            new_srt_path = (
                f"./musicVideoOutput/{artist_safe}/{title_safe}.{language_code}"
            )
            shutil.move(srt_file, new_srt_path)
    # endregion

    # region Create NFO file
    nfo_content = create_nfo(artists[0], title, f"{title_safe}.jpg")

    if not nfo_content:
        return True

    nfo_path = f"./musicVideoOutput/{artist_safe}/{title_safe}.nfo"
    with open(nfo_path, "w") as nfo_file:
        nfo_file.write(nfo_content)
    # endregion
    return True


def download_music_video(title: str, artists: list, album: str = None):
    mv_config = config.MUSICVIDEO

    if not mv_config.enabled:
        return False

    if os.path.exists(
        f"./musicVideoOutput/{make_filename_safe(artists[0])}/{make_filename_safe(title)}.jpg"
    ):
        return True

    print(f"Downloading {title} by {artists[0]}")

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
            logging_manager.log(
                f"Error downloading music video: {e}", level=logging.ERROR
            )
            existing_data.downloadError = 1
            db.commit()
            return False

    if (
        not mv_config.use_youtube_search
        and not mv_config.use_shazam_search
        and not mv_config.use_imvdb
    ):
        raise NotImplementedError("No search method is enabled")

    youtube_id, additional_info = None, None
    if mv_config.use_imvdb:
        youtube_id, additional_info = imvdb_search(
            title=title, artists=artists, album=album
        )
    if youtube_id is None and mv_config.use_shazam_search:
        youtube_id = shazam_cdn_search(title=title, artists=artists)
    if youtube_id is None and mv_config.use_youtube_search:
        raise NotImplementedError("Youtube search is not yet implemented")

    db_addition = musicVideoCache(
        youtubeId=youtube_id,
        title=title,
        artists=artists,
        album=album,
        additionalInfo=additional_info,
        dateAdded=round(time.time()),
    )

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
