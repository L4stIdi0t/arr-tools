import os
import shutil

import requests
import yt_dlp

from shazam_api import shazam_confirm_song
from utils.config_manager import ConfigManager
from utils.log_manager import LoggingManager

# region Configuration and Setup
config_manager = ConfigManager()
config = config_manager.get_config()
logging_manager = LoggingManager()

# endregion

os.makedirs("./temp/downloading", exist_ok=True)
shutil.rmtree("./temp/downloading", ignore_errors=True)  # Cleanup old downloads if any


def download_music_video(youtube_id: str, title: str, artists: list, album: str = None, additional_info: dict = None):
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
    thumbnail_url = f"https://i.ytimg.com/vi/{youtube_id}/maxresdefault.jpg"
    thumbnail_path = f"./musicVideoOutput/{artists[0]}/{title}.jpg"
    response = requests.get(thumbnail_url)
    if response.status_code == 200:
        with open(thumbnail_path, "wb") as thumbnail_file:
            thumbnail_file.write(response.content)

    os.makedirs(f"./musicVideoOutput/{artists[0]}", exist_ok=True)
    shutil.move(f"./temp/downloading/{youtube_id}.mp4", f"./musicVideoOutput/{artists[0]}/{title}.mp4")
