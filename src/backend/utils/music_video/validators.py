from utils.config_manager import ConfigManager
from utils.log_manager import LoggingManager
from utils.validators import normalize_string, fuzzy_str_match

# region Configuration and Setup
config_manager = ConfigManager()
config = config_manager.get_config()
logging_manager = LoggingManager()


# endregion


def validate_youtube_title(title: str, song_title: str, song_artists: list):
    mv_config = config.MUSICVIDEO
    title = normalize_string(title)

    score = 100

    if any(
        fuzzy_str_match(title, bad_keyword) for bad_keyword in mv_config.bad_keywords
    ):
        return False
    for good_keyword in mv_config.good_keywords:
        if fuzzy_str_match(title, good_keyword):
            score += 1
    for bad_keyword in mv_config.bad_keywords:
        if fuzzy_str_match(title, bad_keyword):
            score -= 1

    title = " ".join("".join(e for e in title if e.isalnum() or e.isspace()).split())
    title_words = title.split(" ")

    song_title = " ".join(
        "".join(e for e in song_title if e.isalnum() or e.isspace()).split()
    )
    song_title_words = song_title.split(" ")

    for song_word in song_title_words:
        if not any(
            fuzzy_str_match(song_word, title_word) for title_word in title_words
        ):
            return False

    artists = " ".join(map(str, song_artists))
    artists = " ".join(
        "".join(e for e in artists if e.isalnum() or e.isspace()).split()
    )
    artists_words = artists.split(" ")

    for title_word in title_words:
        if any(
            fuzzy_str_match(title_word, artist_word) for artist_word in artists_words
        ):
            return score
