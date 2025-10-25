import asyncio
from io import BytesIO

import requests
import shazamio
from pydub import AudioSegment
from random_user_agent.params import OperatingSystem
from random_user_agent.user_agent import UserAgent

from utils.music_video.validators import validate_youtube_title

user_agent_rotator = UserAgent(
    operating_systems=[OperatingSystem.ANDROID.value, OperatingSystem.IOS.value],
    limit=100,
)


def shazam_cdn_search(title: str, artists: list, track_id: int = 0):
    youtube_cdn_url = f'https://cdn.shazam.com/video/v3/-/GB/web/{track_id}/youtube/video?q={"+".join(artists)}+%22{title}%22'
    youtube_cdn_url = youtube_cdn_url.replace(" ", "+")

    HEADERS = {
        "X-Shazam-Platform": "IPHONE",
        "X-Shazam-AppVersion": "14.1.0",
        "Accept": "*/*",
        "Accept-Language": "en",
        "Accept-Encoding": "gzip, deflate",
        "User-Agent": user_agent_rotator.get_random_user_agent(),
    }

    cdn_data = requests.get(url=youtube_cdn_url, headers=HEADERS)
    if cdn_data.status_code != 200:
        return None

    cdn_data = cdn_data.json()
    youtube_url = cdn_data.get("actions", None)[0].get("uri", None)
    if youtube_url is not None and "youtu" in youtube_url:
        if not validate_youtube_title(cdn_data.get("caption"), title, artists):
            return None
        youtube_url = youtube_url.replace("https://youtu.be/", "")
        youtube_url = youtube_url.replace("?autoplay=1", "")
        return youtube_url
    else:
        return None


def shazam_confirm_song(
    file_path: str, song_name: str, artists: list, album: str = None
):
    shazam = shazamio.Shazam()
    try:
        audio_data = None
        audio_segment = None

        # Read and decode mp4 file
        with open(file_path, "rb") as f:
            mp4_data = f.read()

        for i in range(3):
            if i == 0:
                audio_bytes = mp4_data
            else:
                if not audio_data:
                    audio_data = BytesIO(mp4_data)
                    audio_segment = AudioSegment.from_file(audio_data, format="mp4")

                if i == 1:
                    half_audio = audio_segment[5_000:10_000]
                elif i == 2:
                    half_audio = audio_segment[30_000:42_000]
                else:
                    raise Exception("This many loops is not implemented yet")

                buffer = half_audio.export(format="ogg")
                buffer = BytesIO()
                half_audio.export(buffer, format="mp4")
                audio_bytes = buffer.getvalue()

            recognized_track_info = asyncio.run(shazam.recognize(audio_bytes))
            track_title = recognized_track_info.get("track", {}).get("title", None)
            track_artist = recognized_track_info.get("track", {}).get("subtitle", None)
            if validate_youtube_title(
                f"{track_title} {track_artist}", song_name, artists
            ):
                return True
        return False
    except Exception as e:
        return None
