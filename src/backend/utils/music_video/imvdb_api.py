import requests
from random_user_agent.user_agent import UserAgent

from utils.validators import fuzzy_str_match

user_agent_rotator = UserAgent(limit=100)


def imvdb_search(artists: list, title: str, album: str):
    url = f'https://imvdb.com/api/v1/search/videos?q={"+".join(artists)}+{title}'
    HEADERS = {
        "User-Agent": user_agent_rotator.get_random_user_agent(),
        "Accept": "application/json, text/plain, */*",
    }

    response = requests.get(url=url, headers=HEADERS)
    if response.status_code == 429:
        raise NotImplementedError("Rate limit exceeded")
    if response.status_code != 200:
        return None, None

    results = response.json()["results"]
    imvdb_id = None
    for result in results:
        artist_match = any(
            fuzzy_str_match(artist, str(result_artist["name"]))
            for artist in artists
            for result_artist in result["artists"]
        )
        try:
            title_match = fuzzy_str_match(title, str(result["song_title"]))
        except:
            print(result)
            raise
        if artist_match and title_match:
            imvdb_id = result["id"]
            break

    if imvdb_id is None:
        return None, None

    url = f"https://imvdb.com/api/v1/video/{imvdb_id}?include=sources,featured,credits,popularity"
    response = requests.get(url=url, headers=HEADERS)
    if response.status_code == 429:
        raise NotImplementedError("Rate limit exceeded")
    if response.status_code != 200:
        return None, None

    result = response.json()
    youtube_id = None
    for source in result["sources"]:
        if source["source"] == "youtube":
            youtube_id = source["source_data"]
            break
    if youtube_id is None:
        return None, None

    return youtube_id, {
        "year": result["year"],
        "artists": [artist["name"] for artist in result["artists"]],
        "featured_artists": [artist["name"] for artist in result["featured_artists"]],
        "views_all_time": result["popularity"]["views_all_time"],
    }
