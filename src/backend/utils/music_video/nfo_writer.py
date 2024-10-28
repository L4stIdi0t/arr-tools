import requests

from utils.config_manager import ConfigManager

# TODO: Fix that it does not work with media server

# region Configuration and Setup
config_manager = ConfigManager()
config = config_manager.get_config()


# endregion


MUSICBRAINZ_HEADERS = {'User-Agent': 'Arr-Tools/0.1.0 (https://github.com/L4stIdi0t/arr-tools)'}


def get_lastfm_data(artist: str, title: str):
    url = f"https://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={config.MUSICVIDEO.lastfm_api_key}&artist={artist}&track={title}&format=json"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json().get('track', None)


def get_musicbrainz_release_date(artist: str, title: str):
    url = f"https://musicbrainz.org/ws/2/release/?query=artist:{artist} AND title:{title}&fmt=json"
    response = requests.get(url, headers=MUSICBRAINZ_HEADERS)
    if response.status_code != 200:
        return None
    try:
        return response.json()['releases'][0]['date'].split('-')[0]
    except:
        return None


import xml.sax.saxutils as saxutils

def create_nfo(artist: str, title: str, thumb_relative_path: str):
    safe_artist = saxutils.escape(artist)
    safe_title = saxutils.escape(title)

    lastfm_data = get_lastfm_data(artist, title)

    if not lastfm_data:
        return f"""
        <?xml version="1.0" encoding="utf-8" standalone="yes"?>
        <musicvideo>
            <title>{safe_title}</title>
            <artist>{safe_artist}</artist>
            <year />
            <plot />
            <outline />
            <userrating />
            <track />
            <studio />
            <premiered />
            <lockdata>true</lockdata>
            <thumb>{thumb_relative_path}</thumb>
            <source>youtube</source>
        </musicvideo>
        """

    genre_tags = ''.join(f'    <genre>{genre["name"]}</genre>\n' for genre in lastfm_data['toptags']['tag'][:3]).strip()

    year_tag = '<year />'
    year = get_musicbrainz_release_date(artist, title)
    if year:
        year_tag = f'<year>{year}</year>'

    return f"""
<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<musicvideo>
    <title>{safe_title}</title>
    <artist>{safe_artist}</artist>
    <plot />
    <outline />
    {year_tag}
    <userrating />
    <track />
    <studio />
    <premiered />
    <lockdata>true</lockdata>
    {genre_tags}
    <albumArtistCredits>
        <artist>{saxutils.escape(lastfm_data['artist']['name'])}</artist>
        {f"<musicBrainzArtistID>{lastfm_data['artist']['mbid']}</musicBrainzArtistID>" if 'mbid' in lastfm_data['artist'] else ''}
    </albumArtistCredits>
    <thumb>{thumb_relative_path}</thumb>
    <source>youtube</source>
</musicvideo>
"""
