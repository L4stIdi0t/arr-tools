import datetime
import re

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from database.database import get_program_db
from models.media import FavoriteMovies, FavoriteSeries, OnResumeMovies, OnResumeSeries, PlayedMovies, PlayedSeries, \
    PlayedEpisodes
from utils.custom_emby_api import EmbyAPI


class MediaServerinteracter:
    def __init__(self, media_server_type, media_server_base_url, media_server_api_key):
        self.media_server_type = media_server_type
        self.media_server_base_url = media_server_base_url
        self.media_server_api_key = media_server_api_key

        if self.media_server_type == "emby" or self.media_server_type == "jellyfin":
            self.client = EmbyAPI(self.media_server_api_key, self.media_server_base_url)
        else:
            raise Exception("Media server type not supported " + self.media_server_type)

        if self.test_connection():
            self.client_users = self.client.get_users()

        self.db: Session = next(get_program_db())

    def test_connection(self):
        if self.media_server_type == "emby" or self.media_server_type == "jellyfin":
            try:
                if self.client.test_connection().get("Version", None):
                    return True
                else:
                    return False
            except:
                return False
        else:
            raise Exception("Media server type not supported " + self.media_server_type)

    def _get_numbers_from_string(self, input_string):
        # Use regular expression to extract numbers
        numbers = re.findall(r"\d+", input_string)

        # Convert the extracted numbers from strings to integers
        numbers = [int(num) for num in numbers]
        return numbers

    def get_users(self):
        users = None

        if self.media_server_type == "emby" or self.media_server_type == "jellyfin":
            self.client_users = self.client.get_users()

            keys_to_keep = ["Name", "Id"]
            users = [{key: d[key] for key in keys_to_keep} for d in self.client_users]

        return users

    def update_db(self, user_id, items, table):
        utc_now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        for item in items:
            media_id = item['Id']
            media_name = item['Name']

            # Check if the favorite already exists in the database
            existing_item = self.db.query(table).filter_by(mediaId=media_id).first()

            if existing_item:
                if user_id not in existing_item.userIds:
                    existing_item.userIds.append(user_id)
                    existing_item.date = utc_now
                    flag_modified(existing_item, "userIds")
            else:
                new_favorite = table(
                    name=media_name,
                    mediaId=media_id,
                    userIds=[user_id],
                    date=utc_now
                )
                self.db.add(new_favorite)

        # Remove the user ID from items they no longer favorite
        item_ids = [item['Id'] for item in items]
        for item in self.db.query(table).all():
            if str(item.mediaId) not in str(item_ids):
                if user_id in item.userIds:
                    item.userIds.remove(user_id)
                    if not item.userIds:
                        self.db.delete(item)
                    else:
                        flag_modified(item, "userIds")
        self.db.commit()

    def update_favorites(self):
        if self.media_server_type == "emby" or self.media_server_type == "jellyfin":
            for user in self.client_users:
                user_id = user["Id"]
                user_favorites = self.client.get_user_favorites(user_id)
                movies = [d for d in user_favorites if d["Type"] == "Movie"]
                series = [d for d in user_favorites if d["Type"] == "Series"]

                self.update_db(user_id, movies, FavoriteMovies)
                self.update_db(user_id, series, FavoriteSeries)

    def get_all_favorites(self, ignore_user_ids=[]):
        try:
            self.update_favorites()
        except:
            pass

        ignore_user_ids_set = set(ignore_user_ids)
        favorites = {"Movies": [], "Series": []}

        movie_rows = self.db.query(FavoriteMovies).all()
        for serie in movie_rows:
            userIds_set = set(serie.userIds)
            if len(userIds_set - ignore_user_ids_set) == 0:
                continue
            favorites['Movies'].append(
                {
                    "Name": serie.name,
                    "Id": serie.mediaId,
                    "Date": datetime.datetime.fromtimestamp(serie.date, tz=datetime.timezone.utc)
                }
            )
        serie_rows = self.db.query(FavoriteSeries).all()
        for serie in serie_rows:
            userIds_set = set(serie.userIds)
            if len(userIds_set - ignore_user_ids_set) == 0:
                continue
            favorites['Series'].append(
                {
                    "Name": serie.name,
                    "Id": serie.mediaId,
                    "Date": datetime.datetime.fromtimestamp(serie.date, tz=datetime.timezone.utc)
                }
            )

        return favorites

    def update_on_resume(self):
        if self.media_server_type == "emby" or self.media_server_type == "jellyfin":
            for user in self.client_users:
                user_id = user["Id"]
                user_favorites = self.client.get_user_resume(user["Id"])
                movies = [d for d in user_favorites if d["Type"] == "Movie"]
                episodes = [d for d in user_favorites if d["Type"] == "Episode"]
                series = []
                for serie in episodes:
                    new_format = {}
                    new_format["Name"] = serie["SeriesName"]
                    new_format["Id"] = serie["SeriesId"]
                    series.append(new_format)

                self.update_db(user_id, movies, OnResumeMovies)
                self.update_db(user_id, series, OnResumeSeries)

    def get_on_resume(self, ignore_user_ids=[]):
        try:
            self.update_on_resume()
        except:
            pass

        ignore_user_ids_set = set(ignore_user_ids)
        favorites = {"Movies": [], "Series": []}

        movie_rows = self.db.query(OnResumeMovies).all()
        for movie in movie_rows:
            userIds_set = set(movie.userIds)
            if len(userIds_set - ignore_user_ids_set) == 0:
                continue
            favorites['Movies'].append(
                {
                    "Name": movie.name,
                    "Id": movie.mediaId,
                    "Date": datetime.datetime.fromtimestamp(movie.date, tz=datetime.timezone.utc)
                }
            )
        serie_rows = self.db.query(OnResumeSeries).all()
        for serie in serie_rows:
            userIds_set = set(serie.userIds)
            if len(userIds_set - ignore_user_ids_set) == 0:
                continue
            favorites['Series'].append(
                {
                    "Name": serie.name,
                    "Id": serie.mediaId,
                    "Date": datetime.datetime.fromtimestamp(serie.date, tz=datetime.timezone.utc)
                }
            )

        return favorites

    def update_played(self):
        if self.media_server_type == "emby" or self.media_server_type == "jellyfin":
            for user in self.client_users:
                user_id = user["Id"]
                user_played = self.client.get_user_played(user["Id"])
                movies = [d for d in user_played if d["Type"] == "Movie"]
                series = [d for d in user_played if d["Type"] == "Series"]
                episodes = [d for d in user_played if d["Type"] == "Episode"]
                episodes_formatted = []
                for episode in episodes:
                    new_format = {}
                    new_format["Name"] = episode["SeriesName"]
                    new_format["Id"] = f'{episode["SeriesId"]}S{episode["ParentIndexNumber"]}E{episode["IndexNumber"]}'
                    episodes_formatted.append(new_format)

                self.update_db(user_id, movies, PlayedMovies)
                self.update_db(user_id, series, PlayedSeries)
                self.update_db(user_id, episodes_formatted, PlayedEpisodes)

    def get_played(self, ignore_user_ids=[]):
        try:
            self.update_played()
        except:
            pass

        ignore_user_ids_set = set(ignore_user_ids)
        played = {"Movies": [], "Series": [], "Episodes": []}

        movie_rows = self.db.query(PlayedMovies).all()
        for movie in movie_rows:
            userIds_set = set(movie.userIds)
            if len(userIds_set - ignore_user_ids_set) == 0:
                continue
            played['Movies'].append(
                {
                    "Name": movie.name,
                    "Id": movie.mediaId,
                    "Date": datetime.datetime.fromtimestamp(movie.date, tz=datetime.timezone.utc)
                }
            )
        serie_rows = self.db.query(PlayedSeries).all()
        for serie in serie_rows:
            userIds_set = set(serie.userIds)
            if len(userIds_set - ignore_user_ids_set) == 0:
                continue
            played['Series'].append(
                {
                    "Name": serie.name,
                    "Id": serie.mediaId,
                    "Date": datetime.datetime.fromtimestamp(serie.date, tz=datetime.timezone.utc)
                }
            )
        episode_rows = self.db.query(PlayedEpisodes).all()
        for episode in episode_rows:
            userIds_set = set(episode.userIds)
            if len(userIds_set - ignore_user_ids_set) == 0:
                continue
            split = episode.mediaId.split('S')
            _id = split[0]
            split = split[1].split('E')
            season_number = split[0]
            episode_number = split[1]
            played['Episodes'].append(
                {
                    "Name": episode.name,
                    "Id": _id,
                    "Season": season_number,
                    "Episode": episode_number,
                    "Date": datetime.datetime.fromtimestamp(episode.date, tz=datetime.timezone.utc)
                }
            )

        return played

    def get_max_played_episodes(self, ignore_user_ids=[]):
        try:
            self.update_played()
        except:
            pass

        ignore_user_ids_set = set(ignore_user_ids)
        episode_rows = self.db.query(PlayedEpisodes).all()

        max_episodes_per_show_per_user = {}

        for episode in episode_rows:
            user_ids_set = set(episode.userIds)
            if len(user_ids_set - ignore_user_ids_set) == 0:
                continue

            split = episode.mediaId.split('S')
            _id = split[0]
            split = split[1].split('E')
            season_number = int(split[0])
            episode_number = int(split[1])

            for user_id in user_ids_set:
                if user_id in ignore_user_ids_set:
                    continue

                show_key = (user_id, _id)
                current_episode = {
                    "Season": season_number,
                    "Episode": episode_number
                }

                if show_key not in max_episodes_per_show_per_user:
                    max_episodes_per_show_per_user[show_key] = {
                        "Name": episode.name,
                        "Id": _id,
                        "Episodes": [current_episode],
                        "Date": datetime.datetime.fromtimestamp(episode.date, tz=datetime.timezone.utc)
                    }
                else:
                    # Check if the current episode is higher
                    max_season = max_episodes_per_show_per_user[show_key]["Episodes"][-1]["Season"]
                    max_episode = max_episodes_per_show_per_user[show_key]["Episodes"][-1]["Episode"]
                    if (season_number > max_season) or (
                            season_number == max_season and episode_number > max_episode):
                        max_episodes_per_show_per_user[show_key]["Episodes"][-1] = current_episode
                        max_episodes_per_show_per_user[show_key]["Date"] = datetime.datetime.fromtimestamp(
                            episode.date, tz=datetime.timezone.utc)

        # Combine episodes by show
        combined_episodes = {}
        for key, value in max_episodes_per_show_per_user.items():
            show_id = value["Id"]
            if show_id not in combined_episodes:
                combined_episodes[show_id] = value
            else:
                combined_episodes[show_id]["Episodes"].append(value["Episodes"][-1])

        return list(combined_episodes.values())

    def unmark_favorite_played_items(self, played_item_types=["Episode"]):
        if self.media_server_type == "emby" or self.media_server_type == "jellyfin":
            for user in self.client_users:
                user_id = user["Id"]
                favorites = self.client.get_user_favorites(user["Id"])
                favorites = [
                    d for d in favorites if d["Type"] in played_item_types
                ]
                for favorite in favorites:
                    if favorite['UserData']['Played']:
                        self.client.unmark_item_as_favorite(user_id, favorite["Id"])
        else:
            raise Exception("Media server type not supported " + self.media_server_type)
