import datetime
import re
import time
from typing import Dict, List, Set, Tuple, Any, Optional

from pyarr import RadarrAPI
from sqlalchemy.orm import Session

from database.database import get_program_db
from utils.config_manager import ConfigManager
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
radarr = None
db: Session = next(get_program_db())

# Cache for movie data to improve performance
movie_cache = {}
# Search history with timestamps for cooldown implementation
search_history = {}


class RadarrManager:
    """
    Class to manage Radarr operations with improved memory efficiency and performance.
    """

    def __init__(self):
        self.config = ConfigManager().get_config()
        self.now_time = datetime.datetime.now(datetime.timezone.utc)
        self.arr_items = []
        self.exclude_tags_from_monitoring = set(
            self.config.RADARR.exclude_tags_from_monitoring
        )
        self.exclude_tags_from_quality_upgrades = set(
            self.config.RADARR.exclude_tags_from_quality_upgrades
        )
        self.exclude_tags_from_deletion = set(
            self.config.RADARR.exclude_tags_from_deletion
        )

    def get_quality_changes(self) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Determines quality profile changes for movies.

        Returns:
            Tuple containing quality changes, monitor items, and unmonitor items
        """
        quality_items = []
        unmonitor = []

        watched_items = []
        favorited_items = []
        on_resume_items = []

        if self.config.RADARR.use_watched:
            watched_items = media_server.get_played(
                ignore_user_ids=self.config.RADARR.exclude_users_from_quality_upgrades
            )["Movies"]
        if self.config.RADARR.use_favorite:
            favorited_items = media_server.get_all_favorites(
                ignore_user_ids=self.config.RADARR.exclude_users_from_quality_upgrades
            )["Movies"]
        if self.config.RADARR.use_on_resume:
            on_resume_items = media_server.get_on_resume(
                ignore_user_ids=self.config.RADARR.exclude_users_from_quality_upgrades
            )["Movies"]

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
        on_resume_items = [
            arr_item
            for item in on_resume_items
            if (arr_item := link_arr_to_media_server(item, self.arr_items)) is not None
        ]

        # Here should the decaying of watched items be implemented...
        quality_items += classify_items_by_decay(
            items=watched_items,
            decay_days=self.config.RADARR.watched_decay_days,
            decay_start_timer=self.config.RADARR.decay_start_timer,
            played_items=watched_items,
            quality_profile=self.config.RADARR.watched_quality_profile,
        )
        quality_items += classify_items_by_decay(
            favorited_items,
            self.config.RADARR.favorite_decay_days,
            self.config.RADARR.decay_start_timer,
            favorited_items,
            self.config.RADARR.favorited_quality_profile,
        )
        quality_items += classify_items_by_decay(
            on_resume_items,
            self.config.RADARR.on_resume_decay_days,
            self.config.RADARR.decay_start_timer,
            on_resume_items,
            self.config.RADARR.on_resume_quality_profile,
        )

        # region Filters
        filters = self.config.RADARR.popular_filters
        very_popular_items = filter_items(self.arr_items, filters["very_popular"])
        popular_items = filter_items(self.arr_items, filters["popular"])
        less_popular_items = filter_items(self.arr_items, filters["less_popular"])
        unpopular_items = filter_items(self.arr_items, filters["unpopular"])
        reassign_based_on_age(
            very_popular_items,
            self.config.RADARR.very_popular_decay_days,
            self.config.RADARR.decay_start_timer,
            watched_items,
            very_popular_items,
            popular_items,
        )
        reassign_based_on_age(
            popular_items,
            self.config.RADARR.popular_decay_days,
            self.config.RADARR.decay_start_timer,
            watched_items,
            popular_items,
            less_popular_items,
        )
        reassign_based_on_age(
            less_popular_items,
            self.config.RADARR.less_popular_decay_days,
            self.config.RADARR.decay_start_timer,
            watched_items,
            less_popular_items,
            unpopular_items,
        )
        reassign_based_on_age(
            unpopular_items,
            self.config.RADARR.unpopular_decay_days,
            self.config.RADARR.decay_start_timer,
            watched_items,
            unpopular_items,
            unmonitor,
        )

        quality_items.append(
            (self.config.RADARR.very_popular_quality_profile, very_popular_items)
        )
        quality_items.append(
            (self.config.RADARR.popular_quality_profile, popular_items)
        )
        quality_items.append(
            (self.config.RADARR.less_popular_quality_profile, less_popular_items)
        )
        quality_items.append(
            (self.config.RADARR.unpopular_quality_profile, unpopular_items)
        )
        # endregion

        quality_items.append((-1, unmonitor))

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
                quality_id = self.config.RADARR.low_quality_profile
            elif tuple_item[0] == 1:
                quality_id = self.config.RADARR.normal_quality_profile
            elif tuple_item[0] == 2:
                quality_id = self.config.RADARR.high_quality_profile
            elif tuple_item[0] == 3:
                quality_id = self.config.RADARR.ultra_quality_profile

            if quality_id is None:
                print(f"Configuration for {tuple_item[0]} quality id is bad")
                continue

            for item in tuple_item[1]:
                if item["qualityProfileId"] != quality_id:
                    quality_changes.append(
                        {"item": item, "new_quality_profile": quality_id}
                    )
                else:
                    monitor_items.append(item)

        return quality_changes, monitor_items, unmonitor_items

    def get_monitorable_items(self) -> Tuple[List[Dict], List[Dict]]:
        """
        Identifies items to monitor/unmonitor.

        Returns:
            Tuple containing monitor and unmonitor items
        """
        favorited_items = []
        on_resume_items = []
        very_popular_items = []
        popular_items = []
        less_popular_items = []
        unpopular_items = []
        unmonitor = []

        watched_items = media_server.get_played(
            ignore_user_ids=self.config.RADARR.exclude_users_from_quality_upgrades
        )["Movies"]
        if (
            self.config.RADARR.use_favorite
            and self.config.RADARR.mark_favorited_as_monitored
        ):
            favorited_items = media_server.get_all_favorites(
                ignore_user_ids=self.config.RADARR.exclude_users_from_monitoring
            )["Movies"]
        if (
            self.config.RADARR.use_on_resume
            and self.config.RADARR.mark_on_resume_as_monitored
        ):
            on_resume_items = media_server.get_on_resume(
                ignore_user_ids=self.config.RADARR.exclude_users_from_monitoring
            )["Movies"]

        favorited_items = [
            arr_item
            for item in favorited_items
            if (arr_item := link_arr_to_media_server(item, self.arr_items)) is not None
        ]
        on_resume_items = [
            arr_item
            for item in on_resume_items
            if (arr_item := link_arr_to_media_server(item, self.arr_items)) is not None
        ]

        filters = self.config.RADARR.popular_filters
        if self.config.RADARR.mark_very_popular_as_monitored:
            very_popular_items = filter_items(self.arr_items, filters["very_popular"])
        if self.config.RADARR.mark_popular_as_monitored:
            popular_items = filter_items(self.arr_items, filters["popular"])
        if self.config.RADARR.mark_less_popular_as_monitored:
            less_popular_items = filter_items(self.arr_items, filters["less_popular"])
        if (
            self.config.RADARR.mark_unpopular_as_monitored
            or self.config.RADARR.mark_unpopular_as_unmonitored
        ):
            unpopular_items = filter_items(self.arr_items, filters["unpopular"])
        reassign_based_on_age(
            very_popular_items,
            self.config.RADARR.very_popular_decay_days,
            self.config.RADARR.decay_start_timer,
            watched_items,
            very_popular_items,
            popular_items,
        )
        reassign_based_on_age(
            popular_items,
            self.config.RADARR.popular_decay_days,
            self.config.RADARR.decay_start_timer,
            watched_items,
            popular_items,
            less_popular_items,
        )
        reassign_based_on_age(
            less_popular_items,
            self.config.RADARR.less_popular_decay_days,
            self.config.RADARR.decay_start_timer,
            watched_items,
            less_popular_items,
            unpopular_items,
        )
        reassign_based_on_age(
            unpopular_items,
            self.config.RADARR.unpopular_decay_days,
            self.config.RADARR.decay_start_timer,
            watched_items,
            unpopular_items,
            unmonitor,
        )

        monitor = (
            favorited_items
            + on_resume_items
            + very_popular_items
            + popular_items
            + less_popular_items
        )
        if self.config.RADARR.mark_unpopular_as_monitored:
            monitor += unpopular_items
        if self.config.RADARR.mark_unpopular_as_unmonitored:
            unmonitor += unpopular_items

        return monitor, unmonitor

    def change_quality(self, quality_changes: List[Dict]) -> Set[int]:
        """
        Applies quality changes to movies.

        Args:
            quality_changes: List of quality changes to apply

        Returns:
            Set of movie IDs that need to be searched
        """

        def check_if_quality_exists(quality_id):
            qualities = radarr.get_quality_profile()
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
        if self.config.RADARR.monitor_quality_changes:
            monitor = set()
            for quality_change in quality_changes:
                item = quality_change["item"]
                if bool(set(item["tags"]) & self.exclude_tags_from_monitoring):
                    continue
                monitor.add(item["id"])

            if monitor:
                radarr.upd_movies({"monitored": True, "movieIds": list(monitor)})

        # Apply quality changes
        changed_list = [
            {"qualityProfileId": quality, "movieIds": list(ids)}
            for quality, ids in changed_dict.items()
        ]

        # Store movie IDs for searching after all changes
        search_movie_ids = set()

        for changes in changed_list:
            if not check_if_quality_exists(changes["qualityProfileId"]):
                continue

            radarr.upd_movies(changes)

            if self.config.RADARR.search_for_quality_upgrades:
                search_movie_ids.update(changes["movieIds"])

        return search_movie_ids

    def change_monitoring(
        self, monitoring_changes: List[Dict], monitor: bool
    ) -> Set[int]:
        """
        Changes monitoring status for movies.

        Args:
            monitoring_changes: List of items to change monitoring status
            monitor: Boolean indicating whether to monitor or unmonitor

        Returns:
            Set of movie IDs that need to be searched
        """
        allowed_changes = set()
        for item in monitoring_changes:
            tags_set = set(item["tags"])
            if bool(tags_set & self.exclude_tags_from_monitoring):
                continue
            allowed_changes.add(item["id"])

        if allowed_changes:
            radarr.upd_movies({"monitored": monitor, "movieIds": list(allowed_changes)})

        # Return movie IDs to search if monitoring
        return allowed_changes if monitor else set()

    def search_movies_with_cooldown(self, movie_ids: Set[int]):
        """
        Search for movies with cooldown to prevent excessive searches.

        Args:
            movie_ids: Set of movie IDs to search
        """
        current_time = time.time()
        final_search_ids = set()

        for movie_id in movie_ids:
            # Check if movie has been searched recently
            if movie_id in search_history:
                last_search_times = search_history[movie_id]

                # Remove search times older than 50 minutes
                while (
                    last_search_times and last_search_times[0] < current_time - 3000
                ):  # 50 minutes in seconds
                    last_search_times.pop(0)

                # If less than 2 searches in the last 50 minutes, allow search
                if len(last_search_times) < 2:
                    final_search_ids.add(movie_id)
                    last_search_times.append(current_time)
            else:
                # First search for this movie
                search_history[movie_id] = [current_time]
                final_search_ids.add(movie_id)

        # Perform searches
        for movie_id in final_search_ids:
            radarr.post_command("MoviesSearch", movieIds=[movie_id])


def delete_unmonitored_files(dry: bool = False) -> List[str]:
    """
    Deletes files that are not monitored based on specified criteria.

    Parameters:
        dry (bool): If True, performs a dry run without actually deleting files.

    Returns:
        list: List of deleted items
    """
    global radarr, config

    if radarr is None:
        config = ConfigManager().get_config()
        radarr = RadarrAPI(config.RADARR.base_url, config.RADARR.api_key)

    exclude_tags_set = set(config.RADARR.exclude_tags_from_deletion)
    deletions_done = set()
    deletion_ids = set()

    for movie in radarr.get_movie():
        tags_set = set(movie["tags"])
        if bool(tags_set & exclude_tags_set):
            continue
        if movie["monitored"] or not movie["hasFile"]:
            continue

        deletions_done.add(movie["title"])
        deletion_ids.add(movie["movieFileId"])

    if not dry and len(deletion_ids) > 0:
        radarr.del_movie_file(list(deletion_ids))

    return list(deletions_done)


def check_if_radarr_is_busy() -> bool:
    """
    Checks if Radarr is currently busy with commands.

    Returns:
        bool: True if Radarr is busy, False otherwise
    """
    if radarr is None:
        return False

    commands = radarr.get_command()
    return any(
        "search" in command["name"].lower() and command["status"] != "completed"
        for command in commands
    )


def run(dry: bool = False) -> Optional[Dict[str, Any]]:
    """
    Main entry point for the Radarr worker.

    Args:
        dry: If True, performs a dry run without making changes

    Returns:
        dict: Results of the dry run if dry=True, None otherwise
    """
    global radarr, movie_cache

    try:
        # Initialize Radarr API
        config = ConfigManager().get_config()
        radarr = RadarrAPI(config.RADARR.base_url, config.RADARR.api_key)

        # Skip if Radarr is disabled or busy
        if not config.RADARR.enabled and not dry:
            print("Radarr disabled, doing nothing")
            return
        if check_if_radarr_is_busy() and not dry:
            print("Radarr is busy, doing nothing")
            return

        # Clear cache for fresh data
        movie_cache = {}

        # Initialize manager
        manager = RadarrManager()
        manager.arr_items = radarr.get_movie()

        # Get changes
        quality_changes, monitor, unmonitor = manager.get_quality_changes()
        monitorable_items, unmonitorable_items = manager.get_monitorable_items()

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
                "deletable_items": [],
            }

        # Apply changes and collect movie IDs to search
        search_movie_ids = set()

        # Apply quality changes
        quality_search_ids = manager.change_quality(quality_changes)
        search_movie_ids.update(quality_search_ids)

        # Apply monitoring changes
        monitor_search_ids = manager.change_monitoring(monitorable_items, True)
        search_movie_ids.update(monitor_search_ids)
        # manager.change_monitoring(unmonitorable_items, False)

        # Delete unmonitored files if enabled
        # if config.RADARR.delete_unmonitored_files:
        #     delete_unmonitored_files()

        # Perform searches with cooldown
        manager.search_movies_with_cooldown(search_movie_ids)

        print("Ran the Radarr instance")
        return None

    except Exception as error_message:
        pattern_length_difference = r"pyarr\.exceptions\.PyarrServerError: Internal Server Error: Expected query to return (\d+) rows but returned (\d+)"
        match = re.search(pattern_length_difference, str(error_message))
        if match:
            print("Failed to update Radarr because of difference in length of items")
        print(f"Radarr failed to update retrying later: {error_message}")
        return None
