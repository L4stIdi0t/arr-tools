from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DecayMethod(Enum):
    NONE = 0  # Not used
    DELETE = 1  # Not used
    DELETE_AND_DOWNGRADE = 2
    DOWNGRADE = 3


class Quality(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    ULTRA = 3


class DecayStartTimer(Enum):
    ADDED = 0
    SHORTEST = 1
    WATCHED_ELSE_ADDED = 2
    WATCHED_ELSE_SHORTEST = 3


class SonarrMonitoring(Enum):
    SEASON = 0
    THREE_EPISODES = 1
    SIX_EPISODES = 2
    SERIE = 3


class SonarrSettings(BaseModel):
    base_url: str = "http://sonarr:8989/"
    api_key: str = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    enabled: bool = False

    use_watched: bool = True
    use_favorite: bool = True

    ultra_quality_profile: Optional[int] = Field(default=None)
    high_quality_profile: Optional[int] = Field(default=None)
    normal_quality_profile: Optional[int] = Field(default=None)
    low_quality_profile: Optional[int] = Field(default=None)
    watched_quality_profile: int = 2
    favorited_quality_profile: int = 3
    very_popular_quality_profile: int = 2
    popular_quality_profile: int = 1
    less_popular_quality_profile: int = 0
    unpopular_quality_profile: int = 0
    search_for_quality_upgrades: bool = True
    monitor_quality_changes: bool = True
    exclude_tags_from_quality_upgrades: list = []
    exclude_users_from_quality_upgrades: list = []

    watched_decay_days: int = 30
    favorite_decay_days: int = 180
    very_popular_decay_days: int = 30
    popular_decay_days: int = 60
    less_popular_decay_days: int = 90
    unpopular_decay_days: int = 120
    decay_method: int = 3
    decay_start_timer: int = 3

    mark_favorited_as_monitored: bool = True
    mark_very_popular_as_monitored: bool = True
    mark_popular_as_monitored: bool = True
    mark_less_popular_as_monitored: bool = True
    mark_unpopular_as_monitored: bool = False
    mark_unpopular_as_unmonitored: bool = True
    exclude_tags_from_monitoring: list = []
    exclude_users_from_monitoring: list = []
    monitoring_amount: int = 0
    base_monitoring_amount: int = 1

    delete_unmonitored_files: bool = False
    exclude_tags_from_deletion: list = []

    popular_filters: dict = {"very_popular": [], "popular": [], "less_popular": [], "unpopular": []}


class RadarrSettings(BaseModel):
    base_url: str = "http://radarr:7878/"
    api_key: str = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    enabled: bool = False

    ultra_quality_profile: Optional[int] = Field(default=None)
    high_quality_profile: Optional[int] = Field(default=None)
    normal_quality_profile: Optional[int] = Field(default=None)
    low_quality_profile: Optional[int] = Field(default=None)
    watched_quality_profile: int = 2
    favorited_quality_profile: int = 3
    on_resume_quality_profile: int = 2
    very_popular_quality_profile: int = 2
    popular_quality_profile: int = 1
    less_popular_quality_profile: int = 0
    unpopular_quality_profile: int = 0
    search_for_quality_upgrades: bool = True
    monitor_quality_changes: bool = True
    exclude_tags_from_quality_upgrades: list = []
    exclude_users_from_quality_upgrades: list = []

    use_watched: bool = True
    use_favorite: bool = True
    use_on_resume: bool = False

    watched_decay_days: int = 30
    favorite_decay_days: int = 180
    on_resume_decay_days: int = 14
    very_popular_decay_days: int = 30
    popular_decay_days: int = 60
    less_popular_decay_days: int = 90
    unpopular_decay_days: int = 120
    decay_method: int = 3
    decay_start_timer: int = 3

    mark_favorited_as_monitored: bool = True
    mark_on_resume_as_monitored: bool = False
    mark_very_popular_as_monitored: bool = True
    mark_popular_as_monitored: bool = True
    mark_less_popular_as_monitored: bool = True
    mark_unpopular_as_monitored: bool = False
    mark_unpopular_as_unmonitored: bool = True
    exclude_tags_from_monitoring: list = []
    exclude_users_from_monitoring: list = []

    delete_unmonitored_files: bool = False
    exclude_tags_from_deletion: list = []

    popular_filters: dict = {"very_popular": [], "popular": [], "less_popular": [], "unpopular": []}


class SpotifySettings(BaseModel):
    client_id: str = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    client_secret: str = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    playlists: list = []


class MusicVideoSettings(BaseModel):
    enabled: bool = True
    use_imvdb: bool = True
    use_shazam_search: bool = True
    use_youtube_search: bool = False
    good_keywords: list = ["official", "official video", "music video", "vevo", "uncensured", "uncensored"]
    bad_keywords: list = ["acoustic", "lyrics", "remix"]
    exclude_words: list = [
        "tutorial",
        "cover",
        "lesson",
        "karaoke",
        "lessons",
    ]
    check_song_with_recognition: bool = True
    convert_playlists: list = []


class MediaServerSettings(BaseModel):
    media_server_type: str = "emby"
    media_server_base_url: str = "http://media_server:8096/"
    media_server_api_key: str = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    create_leaving_soon_collections: bool = False


class MiscSettings(BaseModel):
    log_level: str = "INFO"
    config_version: str = "0.1.1"


class Config(BaseModel):
    SONARR: SonarrSettings
    RADARR: RadarrSettings
    SPOTIFY: SpotifySettings
    MUSICVIDEO: MusicVideoSettings
    MEDIASERVER: MediaServerSettings
    MISC: MiscSettings
