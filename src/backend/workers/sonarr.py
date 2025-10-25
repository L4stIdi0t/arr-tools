import datetime
import re
import time
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any, Optional

from sqlalchemy.orm import Session

from database.database import get_program_db
from utils.config_manager import ConfigManager
from utils.customSonarApi import customSonarAPI
from utils.general_arr_actions import (
    reassign_based_on_age,
    link_arr_to_media_server,
    classify_items_by_decay,
    combine_tuples,
    sort_tuples,
    subtract_dicts,
)
from utils.media_server_interaction import MediaServerinteracter
from utils.process_filter import filter_items

# Initialize global variables
config = ConfigManager().get_config()
media_server = MediaServerinteracter(
    config.MEDIASERVER.media_server_type,
    config.MEDIASERVER.media_server_base_url,
    config.MEDIASERVER.media_server_api_key,
)
sonarr = None
db: Session = next(get_program_db())

# Cache for series data to improve performance
series_cache = {}
# Search history with timestamps for cooldown implementation
search_history = {}
# Last time monitored episodes changed for each series
monitored_episodes_history = {}


class SonarrManager:
    """
    Class to manage Sonarr operations with improved memory efficiency and performance.
    """

    def __init__(self):
        self.config = ConfigManager().get_config()
        self.now_time = datetime.datetime.now(datetime.timezone.utc)
        self.arr_items = []
        self.exclude_tags_from_monitoring = set(
            self.config.SONARR.exclude_tags_from_monitoring
        )
        self.exclude_tags_from_quality_upgrades = set(
            self.config.SONARR.exclude_tags_from_quality_upgrades
        )
        self.exclude_tags_from_deletion = set(
            self.config.SONARR.exclude_tags_from_deletion
        )

    def get_quality_changes(self) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Determines quality profile changes for series.

        Returns:
            Tuple containing quality changes, monitor items, and unmonitor items
        """
        quality_items = []
        unmonitor = []

        watched_items = []
        favorited_items = []

        # Get favorited items if enabled
        if self.config.SONARR.use_favorite:
            favorited_items = media_server.get_all_favorites(
                ignore_user_ids=self.config.SONARR.exclude_users_from_quality_upgrades
            )["Series"]

        # Get watched items if enabled
        if self.config.SONARR.use_watched:
            watched_items = media_server.get_played(
                ignore_user_ids=self.config.SONARR.exclude_users_from_quality_upgrades
            )["Series"]
            played_items = media_server.get_played(
                ignore_user_ids=self.config.SONARR.exclude_users_from_monitoring
            )
            watched_items = (
                played_items["Series"] + played_items["Episodes"] + watched_items
            )
            temp = {item["Name"] for item in watched_items}
            watched_items = [{"Name": item} for item in temp]

        # Convert media server format to arr format
        watched_items = [
            arr_item
            for item in watched_items
            if (arr_item := link_arr_to_media_server(item, self.arr_items)) is not None
        ]
        favorited_items = [
            arr_item
            for item in favorited_items
            if (arr_item := link_arr_to_media_server(item, self.arr_items)) is not None
        ]

        # Classify items by decay
        quality_items += classify_items_by_decay(
            items=watched_items,
            decay_days=self.config.SONARR.watched_decay_days,
            decay_start_timer=self.config.SONARR.decay_start_timer,
            played_items=watched_items,
            quality_profile=self.config.SONARR.watched_quality_profile,
        )
        quality_items += classify_items_by_decay(
            favorited_items,
            self.config.SONARR.favorite_decay_days,
            self.config.SONARR.decay_start_timer,
            favorited_items,
            self.config.SONARR.favorited_quality_profile,
        )

        # Apply filters
        filters = self.config.SONARR.popular_filters
        very_popular_items = filter_items(self.arr_items, filters["very_popular"])
        popular_items = filter_items(self.arr_items, filters["popular"])
        less_popular_items = filter_items(self.arr_items, filters["less_popular"])
        unpopular_items = filter_items(self.arr_items, filters["unpopular"])

        # Reassign based on age
        reassign_based_on_age(
            very_popular_items,
            self.config.SONARR.very_popular_decay_days,
            self.config.SONARR.decay_start_timer,
            watched_items,
            very_popular_items,
            popular_items,
        )
        reassign_based_on_age(
            popular_items,
            self.config.SONARR.popular_decay_days,
            self.config.SONARR.decay_start_timer,
            watched_items,
            popular_items,
            less_popular_items,
        )
        reassign_based_on_age(
            less_popular_items,
            self.config.SONARR.less_popular_decay_days,
            self.config.SONARR.decay_start_timer,
            watched_items,
            less_popular_items,
            unpopular_items,
        )
        reassign_based_on_age(
            unpopular_items,
            self.config.SONARR.unpopular_decay_days,
            self.config.SONARR.decay_start_timer,
            watched_items,
            unpopular_items,
            unmonitor,
        )

        # Append items to quality_items
        quality_items.append(
            (self.config.SONARR.very_popular_quality_profile, very_popular_items)
        )
        quality_items.append(
            (self.config.SONARR.popular_quality_profile, popular_items)
        )
        quality_items.append(
            (self.config.SONARR.less_popular_quality_profile, less_popular_items)
        )
        quality_items.append(
            (self.config.SONARR.unpopular_quality_profile, unpopular_items)
        )
        quality_items.append((-1, unmonitor))

        # Process quality items
        combined_data = combine_tuples(quality_items)
        sorted_data = sort_tuples(combined_data)
        subtracted_data = subtract_dicts(sorted_data)

        quality_changes = []
        monitor_items = []
        unmonitor_items = []

        for tuple_item in subtracted_data:
            quality_id = None

            if tuple_item[0] == -1:
                unmonitor_items += tuple_item[1]
                continue
            elif tuple_item[0] == 0:
                quality_id = self.config.SONARR.low_quality_profile
            elif tuple_item[0] == 1:
                quality_id = self.config.SONARR.normal_quality_profile
            elif tuple_item[0] == 2:
                quality_id = self.config.SONARR.high_quality_profile
            elif tuple_item[0] == 3:
                quality_id = self.config.SONARR.ultra_quality_profile

            if quality_id is None:
                print(f"Configuration for {tuple_item[0]} quality id is bad")
                continue

            for item in tuple_item[1]:
                if not item:
                    continue
                if "qualityProfileId" not in item:
                    print(f"Item {item} has no quality profile id")
                    continue
                if item["qualityProfileId"] != quality_id:
                    quality_changes.append(
                        {"item": item, "new_quality_profile": quality_id}
                    )
                else:
                    monitor_items.append(item)

        return quality_changes, monitor_items, unmonitor_items

    def _monitor_episodes_ahead(
        self, episodes, season_number, episode_number, ahead_count, series
    ):
        """
        Helper function to monitor episodes ahead of the current episode.

        Args:
            episodes: List of episodes
            season_number: Current season number
            episode_number: Current episode number
            ahead_count: Number of episodes to monitor ahead
            series: Series information

        Returns:
            List of episode IDs to monitor
        """
        episode_ids = []
        count = 0
        ahead_count += 1
        episodes = sorted(
            episodes, key=lambda ep: (ep["seasonNumber"], ep["episodeNumber"])
        )

        for episode in episodes:
            if (
                season_number == episode["seasonNumber"]
                and episode_number == episode["episodeNumber"]
                and count == 0
            ):
                count += 1

            if count <= ahead_count and count != 0:
                count += 1
                episode_ids.append(
                    {
                        "episode_id": episode["id"],
                        "series_id": series["id"],
                        "monitored": episode["monitored"],
                        "season_number": episode["seasonNumber"],
                        "tags": series["tags"],
                    }
                )

            if count > ahead_count:
                continue

        return episode_ids

    def _monitor_episodes_behind(
        self, episodes, season_number, episode_number, ahead_count, series
    ):
        """
        Helper function to monitor episodes behind the current episode.

        Args:
            episodes: List of episodes
            season_number: Current season number
            episode_number: Current episode number
            ahead_count: Number of episodes to monitor behind
            series: Series information

        Returns:
            List of episode IDs to monitor
        """
        episode_ids = []
        count = 0
        ahead_count += 1
        episodes = sorted(
            episodes, key=lambda ep: (ep["seasonNumber"], ep["episodeNumber"])
        )
        episodes.reverse()

        for episode in episodes:
            if (
                season_number == episode["seasonNumber"]
                and episode_number == episode["episodeNumber"]
                and count == 0
            ):
                count += 1

            if count <= ahead_count and count != 0 and episode["seasonNumber"] != 0:
                count += 1
                episode_ids.append(
                    {
                        "episode_id": episode["id"],
                        "series_id": series["id"],
                        "monitored": episode["monitored"],
                        "season_number": episode["seasonNumber"],
                        "tags": series["tags"],
                    }
                )

            if count > ahead_count:
                continue

        return episode_ids

    def get_monitorable_items(self):
        """
        Identifies items to monitor/unmonitor.

        Returns:
            Tuple containing monitor, unmonitor, monitor_episodes, unmonitor_episodes, and recheck_releases
        """
        favorited_items = []
        unmonitor_episodes = []
        very_popular_items = []
        popular_items = []
        less_popular_items = []
        unpopular_items = []
        unmonitor = []

        # Get favorited items if enabled
        if (
            self.config.SONARR.use_favorite
            and self.config.SONARR.mark_favorited_as_monitored
        ):
            favorited_items = media_server.get_all_favorites(
                ignore_user_ids=self.config.SONARR.exclude_users_from_monitoring
            )["Series"]

        # Get played items
        played_items = media_server.get_played(
            ignore_user_ids=self.config.SONARR.exclude_users_from_monitoring
        )
        played_series = played_items["Series"] + played_items["Episodes"]
        temp = {item["Name"] for item in played_series}
        played_series = [{"Name": item} for item in temp]

        # Convert media server format to arr format
        favorited_items = [
            arr_item
            for item in favorited_items
            if (arr_item := link_arr_to_media_server(item, self.arr_items)) is not None
        ]
        played_series = [
            arr_item
            for item in played_series
            if (arr_item := link_arr_to_media_server(item, self.arr_items)) is not None
        ]

        # Apply filters
        filters = self.config.SONARR.popular_filters
        if self.config.SONARR.mark_very_popular_as_monitored:
            very_popular_items = filter_items(self.arr_items, filters["very_popular"])
        if self.config.SONARR.mark_popular_as_monitored:
            popular_items = filter_items(self.arr_items, filters["popular"])
        if self.config.SONARR.mark_less_popular_as_monitored:
            less_popular_items = filter_items(self.arr_items, filters["less_popular"])
        if (
            self.config.SONARR.mark_unpopular_as_monitored
            or self.config.SONARR.mark_unpopular_as_unmonitored
        ):
            unpopular_items = filter_items(self.arr_items, filters["unpopular"])

        # Reassign based on age
        reassign_based_on_age(
            very_popular_items,
            self.config.SONARR.very_popular_decay_days,
            self.config.SONARR.decay_start_timer,
            played_series,
            very_popular_items,
            popular_items,
        )
        reassign_based_on_age(
            popular_items,
            self.config.SONARR.popular_decay_days,
            self.config.SONARR.decay_start_timer,
            played_series,
            popular_items,
            less_popular_items,
        )
        reassign_based_on_age(
            less_popular_items,
            self.config.SONARR.less_popular_decay_days,
            self.config.SONARR.decay_start_timer,
            played_series,
            less_popular_items,
            unpopular_items,
        )
        reassign_based_on_age(
            unpopular_items,
            self.config.SONARR.unpopular_decay_days,
            self.config.SONARR.decay_start_timer,
            played_series,
            unpopular_items,
            unmonitor,
        )

        # Combine monitor items
        monitor = (
            favorited_items
            + played_series
            + very_popular_items
            + popular_items
            + less_popular_items
        )

        if self.config.SONARR.mark_unpopular_as_monitored:
            monitor += unpopular_items
        if self.config.SONARR.mark_unpopular_as_unmonitored:
            unmonitor += unpopular_items

        # Filter out items with excluded tags
        monitor = [
            item
            for item in monitor
            if not bool(set(item["tags"]) & self.exclude_tags_from_monitoring)
        ]
        unmonitor = [
            item
            for item in unmonitor
            if not bool(set(item["tags"]) & self.exclude_tags_from_monitoring)
        ]

        # Monitor episodes based on users watched episodes
        recheck_releases = []
        max_played_episodes = []
        max_played_episodes_shows = []

        for item in media_server.get_max_played_episodes():
            arr_item = link_arr_to_media_server(item, self.arr_items)
            if not arr_item:
                continue
            max_played_episodes.append(item)
            max_played_episodes_shows.append(arr_item)

        monitor_episodes = []

        for idx in range(len(max_played_episodes)):
            if not max_played_episodes_shows[idx]:
                continue

            tags_set = set(max_played_episodes_shows[idx]["tags"])
            if bool(self.exclude_tags_from_monitoring & tags_set):
                continue

            series_id = max_played_episodes_shows[idx]["id"]

            # Use cache if available
            if series_id in series_cache:
                episodes_data = series_cache[series_id]
            else:
                episodes_data = sonarr.get_episode(series_id, series=True)
                series_cache[series_id] = episodes_data

            # Check for missing files that need to be rechecked
            for episode in episodes_data:
                airdate = self.now_time
                airdate_str = episode.get("airDateUtc", None)
                if airdate_str:
                    airdate = datetime.datetime.strptime(
                        airdate_str, "%Y-%m-%dT%H:%M:%SZ"
                    ).replace(tzinfo=datetime.timezone.utc)
                if (
                    not episode.get("hasFile", True)
                    and episode.get("monitored", False)
                    and airdate < self.now_time
                ):
                    recheck_releases.append(series_id)
                    break

            # Process episodes based on monitoring amount
            max_episode_data = defaultdict(int)
            if self.config.SONARR.base_monitoring_amount == 0:
                for episode in episodes_data:
                    max_episode_data[episode["seasonNumber"]] = max(
                        max_episode_data[episode["seasonNumber"]],
                        episode["episodeNumber"],
                    )

            for episode in episodes_data:
                episode_id = episode["id"]
                monitoring_item = {
                    "episode_id": episode_id,
                    "series_id": series_id,
                    "season_number": episode["seasonNumber"],
                    "tags": max_played_episodes_shows[idx]["tags"],
                    "monitored": episode["monitored"],
                }

                if self.config.SONARR.monitoring_amount == 0 and any(
                    episode["seasonNumber"] == max_episode["Season"]
                    for max_episode in max_played_episodes[idx]["Episodes"]
                ):
                    monitor_episodes.append(monitoring_item)
                # Handle complex monitoring logic
                elif self.config.SONARR.monitoring_amount == 0:
                    for max_episode in max_played_episodes[idx]["Episodes"]:
                        if max_episode["Season"] == episode["seasonNumber"]:
                            if (
                                max_episode_data[max_episode["Season"]]
                                - max_episode["Episode"]
                                <= 3
                            ):
                                for ep in episodes_data:
                                    if any(
                                        ep["seasonNumber"] + 1 == max_episode["Season"]
                                        for max_episode in max_played_episodes[idx][
                                            "Episodes"
                                        ]
                                    ):
                                        monitor_episodes.append(monitoring_item)
                elif self.config.SONARR.monitoring_amount == 3:
                    monitor_episodes.append(monitoring_item)
                else:
                    for max_episode in max_played_episodes[idx]["Episodes"]:
                        if self.config.SONARR.monitoring_amount == 1:
                            monitor_episodes += self._monitor_episodes_ahead(
                                episodes_data,
                                max_episode["Season"],
                                max_episode["Episode"],
                                3,
                                max_played_episodes_shows[idx],
                            )
                            monitor_episodes += self._monitor_episodes_behind(
                                episodes_data,
                                max_episode["Season"],
                                max_episode["Episode"],
                                3,
                                max_played_episodes_shows[idx],
                            )
                        elif self.config.SONARR.monitoring_amount == 2:
                            monitor_episodes += self._monitor_episodes_ahead(
                                episodes_data,
                                max_episode["Season"],
                                max_episode["Episode"],
                                6,
                                max_played_episodes_shows[idx],
                            )
                            monitor_episodes += self._monitor_episodes_behind(
                                episodes_data,
                                max_episode["Season"],
                                max_episode["Episode"],
                                6,
                                max_played_episodes_shows[idx],
                            )

        # Remove series from recheck_releases if it's in monitor_episodes
        series_in_monitor = {item["series_id"] for item in monitor_episodes}
        recheck_releases = [
            item for item in recheck_releases if item not in series_in_monitor
        ]

        # Monitor base amount and create unmonitor episodes
        for arr_item in self.arr_items:
            tags_set = set(arr_item["tags"])
            if bool(self.exclude_tags_from_monitoring & tags_set):
                continue

            series_id = arr_item["id"]

            # Use cache if available
            if series_id in series_cache:
                episodes_data = series_cache[series_id]
            else:
                episodes_data = sonarr.get_episode(series_id, series=True)
                series_cache[series_id] = episodes_data

            for episode in episodes_data:
                episode_id = episode["id"]

                monitoring_item = {
                    "episode_id": episode_id,
                    "series_id": series_id,
                    "season_number": episode["seasonNumber"],
                    "tags": arr_item["tags"],
                    "monitored": episode["monitored"],
                }

                unmonitor_episodes.append(monitoring_item)

                if (
                    episode["seasonNumber"] != 1
                    and self.config.SONARR.base_monitoring_amount != 3
                ):
                    continue

                if (
                    self.config.SONARR.base_monitoring_amount == 0
                    or self.config.SONARR.base_monitoring_amount == 3
                    or (
                        self.config.SONARR.base_monitoring_amount == 1
                        and episode["episodeNumber"] <= 3
                    )
                    or (
                        self.config.SONARR.base_monitoring_amount == 2
                        and episode["episodeNumber"] <= 6
                    )
                ):
                    monitor_episodes.append(monitoring_item)

        # Filter out monitored episodes from unmonitor_episodes
        monitored_ids = {item["episode_id"] for item in monitor_episodes}
        unmonitor_episodes = [
            episode
            for episode in unmonitor_episodes
            if episode["episode_id"] not in monitored_ids
        ]

        return (
            monitor,
            unmonitor,
            monitor_episodes,
            unmonitor_episodes,
            recheck_releases,
        )

    def change_quality(self, quality_changes):
        """
        Applies quality changes to series.

        Args:
            quality_changes: List of quality changes to apply
        """

        def check_if_quality_exists(quality_id):
            qualities = sonarr.get_quality_profile()
            return any(quality["id"] == quality_id for quality in qualities)

        changed_dict = {}
        for quality_change in quality_changes:
            if bool(
                set(quality_change["item"]["tags"])
                & self.exclude_tags_from_quality_upgrades
            ):
                continue

            if quality_change["new_quality_profile"] not in changed_dict:
                changed_dict[quality_change["new_quality_profile"]] = set()
            changed_dict[quality_change["new_quality_profile"]].add(
                quality_change["item"]["id"]
            )

        # Monitor quality changes if enabled
        if self.config.SONARR.monitor_quality_changes:
            monitor = set()
            for quality_change in quality_changes:
                item = quality_change["item"]
                if bool(set(item["tags"]) & self.exclude_tags_from_monitoring):
                    continue
                monitor.add(item["id"])

            if monitor:
                sonarr.upd_series_editor(
                    {"monitored": True, "seriesIds": list(monitor)}
                )

        # Apply quality changes
        changed_list = [
            {"qualityProfileId": quality, "seriesIds": list(ids)}
            for quality, ids in changed_dict.items()
        ]

        # Store series IDs for searching after all changes
        search_series_ids = set()

        for changes in changed_list:
            if not check_if_quality_exists(changes["qualityProfileId"]):
                continue

            sonarr.upd_series_editor(changes)

            if self.config.SONARR.search_for_quality_upgrades:
                search_series_ids.update(changes["seriesIds"])

        return search_series_ids

    def change_monitoring(self, monitoring_changes, monitor):
        """
        Changes monitoring status for series.

        Args:
            monitoring_changes: List of items to change monitoring status
            monitor: Boolean indicating whether to monitor or unmonitor

        Returns:
            Set of series IDs that need to be searched
        """
        allowed_changes = set()
        for item in monitoring_changes:
            tags_set = set(item["tags"])
            if bool(tags_set & self.exclude_tags_from_monitoring):
                continue
            allowed_changes.add(item["id"])

        if allowed_changes:
            sonarr.upd_series_editor(
                {"monitored": monitor, "seriesIds": list(allowed_changes)}
            )

        # Return series IDs to search if monitoring
        return allowed_changes if monitor else set()

    def change_monitoring_episodes(self, monitoring_changes, monitor):
        """
        Changes monitoring status for episodes.

        Args:
            monitoring_changes: List of episodes to change monitoring status
            monitor: Boolean indicating whether to monitor or unmonitor

        Returns:
            Set of series IDs that need to be searched
        """
        search_series = set()

        # Update season monitoring if needed
        if monitor:
            seasons_monitoring = defaultdict(set)
            for item in monitoring_changes:
                tags_set = set(item["tags"])
                if bool(tags_set & self.exclude_tags_from_monitoring):
                    continue
                seasons_monitoring[item["series_id"]].add(item["season_number"])

            for serie_id, seasons in seasons_monitoring.items():
                found_series = next(
                    (item for item in self.arr_items if item["id"] == serie_id), None
                )
                if not found_series:
                    continue

                changed_season = False
                for season in found_series["seasons"]:
                    if season["monitored"]:
                        continue
                    if season["seasonNumber"] in seasons:
                        season["monitored"] = True
                        changed_season = True

                if changed_season:
                    sonarr.upd_series(found_series)

        # Update episode monitoring
        allowed_changes = set()
        for item in monitoring_changes:
            tags_set = set(item["tags"])
            if bool(tags_set & self.exclude_tags_from_monitoring):
                continue
            if item["monitored"] == monitor:
                continue
            allowed_changes.add(item["episode_id"])
            search_series.add(item["series_id"])

        if allowed_changes:
            sonarr.upd_episode_monitor(list(allowed_changes), monitor)

            # Track monitored episodes changes for cooldown override
            if monitor:
                current_time = time.time()
                for item in monitoring_changes:
                    if item["series_id"] in monitored_episodes_history:
                        monitored_episodes_history[item["series_id"]] = current_time

        # Return series IDs to search if monitoring
        return search_series if monitor else set()

    def search_series_with_cooldown(self, series_ids):
        """
        Search for series with cooldown to prevent excessive searches.

        Args:
            series_ids: Set of series IDs to search
        """
        current_time = time.time()
        final_search_ids = set()

        for series_id in series_ids:
            # Check if series has been searched recently
            if series_id in search_history:
                last_search_times = search_history[series_id]

                # If monitored episodes changed, override cooldown
                if (
                    series_id in monitored_episodes_history
                    and monitored_episodes_history[series_id] > last_search_times[-1]
                ):
                    final_search_ids.add(series_id)
                    search_history[series_id].append(current_time)
                    continue

                # Remove search times older than 50 minutes
                while (
                    last_search_times and last_search_times[0] < current_time - 3000
                ):  # 50 minutes in seconds
                    last_search_times.pop(0)

                # If less than 2 searches in the last 50 minutes, allow search
                if len(last_search_times) < 2:
                    final_search_ids.add(series_id)
                    last_search_times.append(current_time)
            else:
                # First search for this series
                search_history[series_id] = [current_time]
                final_search_ids.add(series_id)

        # Perform searches
        for series_id in final_search_ids:
            sonarr.post_command("SeriesSearch", seriesId=series_id)


def delete_unmonitored_files(dry: bool = False, delete: list = ["episode"]):
    """
    Deletes files that are not monitored based on specified criteria.

    Parameters:
    dry (bool): If True, performs a dry run without actually deleting files.
    delete (list): List of types to be deleted. Only episodes enabled

    Returns:
    list: List of deleted items
    """
    global sonarr, config

    if sonarr is None:
        config = ConfigManager().get_config()
        sonarr = customSonarAPI(config.SONARR.base_url, config.SONARR.api_key)

    for type in delete:
        if type != "episode":
            raise NotImplementedError("Only episode type is currently supported")

    exclude_tags_set = set(config.SONARR.exclude_tags_from_deletion)
    deletions_done = set()

    for serie in sonarr.get_series():
        tags_set = set(serie["tags"])
        if bool(tags_set & exclude_tags_set):
            continue

        if "episode" in delete:
            episodes = sonarr.get_episode(serie["id"], series=True)
            for episode in episodes:
                if episode["monitored"] or not episode["hasFile"]:
                    continue
                deletions_done.add(
                    f'{serie["title"]} | S{episode["seasonNumber"]}E{episode["episodeNumber"]}'
                )
                if dry:
                    continue
                sonarr.del_episode_file(episode["episodeFileId"])

    return list(deletions_done)


def run(dry: bool = False):
    """
    Main entry point for the Sonarr worker.

    Args:
        dry: If True, performs a dry run without making changes

    Returns:
        dict: Results of the dry run if dry=True, None otherwise
    """
    global sonarr, series_cache

    try:
        # Initialize Sonarr API
        config = ConfigManager().get_config()
        sonarr = customSonarAPI(config.SONARR.base_url, config.SONARR.api_key)

        # Skip if Sonarr is disabled or busy
        if not config.SONARR.enabled and not dry:
            print("Sonarr disabled, doing nothing")
            return
        if check_if_sonarr_is_busy() and not dry:
            print("Sonarr is busy, doing nothing")
            return

        # Clear cache for fresh data
        series_cache = {}

        # Initialize manager
        manager = SonarrManager()
        manager.arr_items = sonarr.get_series()

        # Get changes
        quality_changes, monitor, unmonitor = manager.get_quality_changes()
        (
            monitorable_items,
            unmonitorable_items,
            monitor_episodes,
            unmonitor_episodes,
            recheck_releases,
        ) = manager.get_monitorable_items()

        # Combine monitor/unmonitor items
        monitorable_items += monitor
        unmonitorable_items += unmonitor
        unmonitorable_items = [
            item
            for item in unmonitorable_items
            if item not in monitorable_items and item.get("monitored", False)
        ]
        monitorable_items = [
            item for item in monitorable_items if not item.get("monitored", False)
        ]

        # Return dry run results if requested
        if dry:
            print("Finished dry run")
            return {
                "quality_changes": quality_changes,
                "monitorable_items": monitorable_items,
                "unmonitorable_items": unmonitorable_items,
                "monitorable_episodes": monitor_episodes,
                "unmonitorable_episodes": unmonitor_episodes,
                "deletable_items": [],
            }

        # Apply changes and collect series IDs to search
        search_series_ids = set()

        # Apply quality changes
        quality_search_ids = manager.change_quality(quality_changes)
        search_series_ids.update(quality_search_ids)

        # Apply monitoring changes
        monitor_search_ids = manager.change_monitoring(monitorable_items, True)
        search_series_ids.update(monitor_search_ids)
        manager.change_monitoring(unmonitorable_items, False)

        # Apply episode monitoring changes
        episode_search_ids = manager.change_monitoring_episodes(monitor_episodes, True)
        search_series_ids.update(episode_search_ids)
        manager.change_monitoring_episodes(unmonitor_episodes, False)

        # Delete unmonitored files if enabled
        if config.SONARR.delete_unmonitored_files:
            delete_unmonitored_files()

        # Add recheck releases to search IDs
        search_series_ids.update(recheck_releases)

        # Perform searches with cooldown
        manager.search_series_with_cooldown(search_series_ids)

        print("Ran the Sonarr instance")
        return None

    except Exception as error_message:
        pattern_length_difference = r"pyarr\.exceptions\.PyarrServerError: Internal Server Error: Expected query to return (\d+) rows but returned (\d+)"
        match = re.search(pattern_length_difference, str(error_message))
        if match:
            print("Failed to update Sonarr because of difference in length of items")
        print(f"Sonarr failed to update retrying later: {error_message}")
        return None


def check_if_sonarr_is_busy():
    """
    Checks if Sonarr is currently busy with commands.

    Returns:
        bool: True if Sonarr is busy, False otherwise
    """
    if sonarr is None:
        return False

    commands = sonarr.get_command()
    return any(
        "search" in command["name"].lower() and command["status"] != "completed"
        for command in commands
    )
