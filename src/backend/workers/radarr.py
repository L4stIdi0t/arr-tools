import datetime
import re

from pyarr import RadarrAPI
from sqlalchemy.orm import Session

from database.database import get_program_db
from utils.config_manager import ConfigManager
from utils.general_arr_actions import reassign_based_on_age, link_arr_to_media_server, \
    classify_items_by_decay, combine_tuples, sort_tuples, subtract_dicts
from utils.media_server_interaction import MediaServerinteracter
from utils.process_filter import filter_items

config = ConfigManager().get_config()

media_server = MediaServerinteracter(config.MEDIASERVER.media_server_type, config.MEDIASERVER.media_server_base_url,
                                     config.MEDIASERVER.media_server_api_key)
radarr = None
arr_items = []
now_time = datetime.datetime.now(datetime.timezone.utc)

db: Session = next(get_program_db())


def get_quality_changes():
    quality_items = []
    unmonitor = []

    watched_items = []
    favorited_items = []
    on_resume_items = []

    if config.RADARR.use_watched:
        watched_items = \
            media_server.get_played(ignore_user_ids=config.RADARR.exclude_users_from_quality_upgrades)["Movies"]
    if config.RADARR.use_favorite:
        favorited_items = \
            media_server.get_all_favorites(ignore_user_ids=config.RADARR.exclude_users_from_quality_upgrades)["Movies"]
    if config.RADARR.use_on_resume:
        on_resume_items = \
            media_server.get_on_resume(ignore_user_ids=config.RADARR.exclude_users_from_quality_upgrades)["Movies"]

    # Convert media server format to arr format
    watched_items = [
        arr_item for item in watched_items
        if (arr_item := link_arr_to_media_server(item, arr_items)) is not None
    ]
    favorited_items = [
        arr_item for item in favorited_items
        if (arr_item := link_arr_to_media_server(item, arr_items)) is not None
    ]
    on_resume_items = [
        arr_item for item in on_resume_items
        if (arr_item := link_arr_to_media_server(item, arr_items)) is not None
    ]

    # Here should the decaying of watched items be implemented...
    quality_items += classify_items_by_decay(items=watched_items, decay_days=config.RADARR.watched_decay_days,
                                             decay_start_timer=config.RADARR.decay_start_timer,
                                             played_items=watched_items,
                                             quality_profile=config.RADARR.watched_quality_profile)
    quality_items += classify_items_by_decay(favorited_items, config.RADARR.favorite_decay_days,
                                             config.RADARR.decay_start_timer, favorited_items,
                                             config.RADARR.favorited_quality_profile)
    quality_items += classify_items_by_decay(on_resume_items, config.RADARR.on_resume_decay_days,
                                             config.RADARR.decay_start_timer, on_resume_items,
                                             config.RADARR.on_resume_quality_profile)

    # region Filters
    filters = config.RADARR.popular_filters
    very_popular_items = filter_items(arr_items, filters["very_popular"])
    popular_items = filter_items(arr_items, filters["popular"])
    less_popular_items = filter_items(arr_items, filters["less_popular"])
    unpopular_items = filter_items(arr_items, filters["unpopular"])
    reassign_based_on_age(very_popular_items, config.RADARR.very_popular_decay_days, config.RADARR.decay_start_timer,
                          watched_items, very_popular_items, popular_items)
    reassign_based_on_age(popular_items, config.RADARR.popular_decay_days, config.RADARR.decay_start_timer,
                          watched_items, popular_items, less_popular_items)
    reassign_based_on_age(less_popular_items, config.RADARR.less_popular_decay_days, config.RADARR.decay_start_timer,
                          watched_items, less_popular_items,
                          unpopular_items)
    reassign_based_on_age(unpopular_items, config.RADARR.unpopular_decay_days, config.RADARR.decay_start_timer,
                          watched_items, unpopular_items, unmonitor)

    quality_items.append((config.RADARR.very_popular_quality_profile, very_popular_items))
    quality_items.append((config.RADARR.popular_quality_profile, popular_items))
    quality_items.append((config.RADARR.less_popular_quality_profile, less_popular_items))
    quality_items.append((config.RADARR.unpopular_quality_profile, unpopular_items))
    # endregion

    quality_items.append((-1, unmonitor))

    combined_data = combine_tuples(quality_items)
    sorted_data = sort_tuples(combined_data)
    subtracted_data = subtract_dicts(sorted_data)

    quality_changes = []
    monitor_items = []
    unmonitor_items = []
    for tuple in subtracted_data:
        quality_id = None

        if tuple[0] == -1:
            unmonitor_items += tuple[1]
            continue
        elif tuple[0] == 0:
            quality_id = config.RADARR.low_quality_profile
        elif tuple[0] == 1:
            quality_id = config.RADARR.normal_quality_profile
        elif tuple[0] == 2:
            quality_id = config.RADARR.high_quality_profile
        elif tuple[0] == 3:
            quality_id = config.RADARR.ultra_quality_profile

        if quality_id is None:
            print(f"Configuration for {tuple[0]} quality id is bad")
            continue

        for item in tuple[1]:
            if item['qualityProfileId'] != quality_id:
                quality_changes.append({'item': item, 'new_quality_profile': quality_id})
            else:
                monitor_items.append(item)

    return quality_changes, monitor_items, unmonitor_items


def get_monitorable_items():
    favorited_items = []
    on_resume_items = []
    very_popular_items = []
    popular_items = []
    less_popular_items = []
    unpopular_items = []
    unmonitor = []

    watched_items = \
        media_server.get_played(ignore_user_ids=config.RADARR.exclude_users_from_quality_upgrades)["Movies"]
    if config.RADARR.use_favorite and config.RADARR.mark_favorited_as_monitored:
        favorited_items = \
            media_server.get_all_favorites(ignore_user_ids=config.RADARR.exclude_users_from_monitoring)["Movies"]
    if config.RADARR.use_on_resume and config.RADARR.mark_on_resume_as_monitored:
        on_resume_items = \
            media_server.get_on_resume(ignore_user_ids=config.RADARR.exclude_users_from_monitoring)["Movies"]

    favorited_items = [
        arr_item for item in favorited_items
        if (arr_item := link_arr_to_media_server(item, arr_items)) is not None
    ]
    on_resume_items = [
        arr_item for item in on_resume_items
        if (arr_item := link_arr_to_media_server(item, arr_items)) is not None
    ]

    filters = config.RADARR.popular_filters
    if config.RADARR.mark_very_popular_as_monitored:
        very_popular_items = filter_items(arr_items, filters["very_popular"])
    if config.RADARR.mark_popular_as_monitored:
        popular_items = filter_items(arr_items, filters["popular"])
    if config.RADARR.mark_less_popular_as_monitored:
        less_popular_items = filter_items(arr_items, filters["less_popular"])
    if config.RADARR.mark_unpopular_as_monitored or config.RADARR.mark_unpopular_as_unmonitored:
        unpopular_items = filter_items(arr_items, filters["unpopular"])
    reassign_based_on_age(very_popular_items, config.RADARR.very_popular_decay_days, config.RADARR.decay_start_timer,
                          watched_items, very_popular_items, popular_items)
    reassign_based_on_age(popular_items, config.RADARR.popular_decay_days, config.RADARR.decay_start_timer,
                          watched_items, popular_items, less_popular_items)
    reassign_based_on_age(less_popular_items, config.RADARR.less_popular_decay_days, config.RADARR.decay_start_timer,
                          watched_items, less_popular_items,
                          unpopular_items)
    reassign_based_on_age(unpopular_items, config.RADARR.unpopular_decay_days, config.RADARR.decay_start_timer,
                          watched_items, unpopular_items, unmonitor)

    monitor = favorited_items + on_resume_items + very_popular_items + popular_items + less_popular_items
    if config.RADARR.mark_unpopular_as_monitored:
        monitor += unpopular_items
    if config.RADARR.mark_unpopular_as_unmonitored:
        unmonitor += unpopular_items

    return monitor, unmonitor


def get_deletable_items():
    # Should be implemented but not yet done
    pass


def change_quality(quality_changes):
    def check_if_quality_exists(quality_id):
        qualities = radarr.get_quality_profile()
        for quality in qualities:
            if quality["id"] == quality_id:
                return True
        return False

    changed_dict = {}
    for quality_change in quality_changes:
        if bool(set(quality_change['item']['tags']) & set(config.RADARR.exclude_tags_from_quality_upgrades)):
            continue

        if quality_change['new_quality_profile'] not in changed_dict:
            changed_dict[quality_change['new_quality_profile']] = set()
        changed_dict[quality_change['new_quality_profile']].add(quality_change['item']['id'])

    if config.RADARR.monitor_quality_changes:
        monitor = set()
        for quality_change in quality_changes:
            item = quality_change['item']
            if bool(set(item['tags']) & set(config.RADARR.exclude_tags_from_monitoring)):
                continue

            monitor.add(item['id'])

        radarr.upd_movies({"monitored": True, "movieIds": list(monitor)})

    changed_list = [
        {"qualityProfileId": quality, "movieIds": list(ids)}
        for quality, ids in changed_dict.items()
    ]

    for changes in changed_list:
        if not check_if_quality_exists(changes['qualityProfileId']):
            continue

        radarr.upd_movies(changes)

        if config.RADARR.search_for_quality_upgrades:
            radarr.post_command("MoviesSearch", movieIds=changes['movieIds'])


def change_monitoring(monitoring_changes: list, monitor: bool):
    allowed_changes = set()
    for item in monitoring_changes:
        tags_set = set(item['tags'])
        exclude_tags_set = set(config.RADARR.exclude_tags_from_monitoring)
        if bool(tags_set & exclude_tags_set):
            continue
        allowed_changes.add(item['id'])

    radarr.upd_movies({"monitored": monitor, "movieIds": list(allowed_changes)})


def delete_unmonitored_files(dry: bool = False):
    """
    Deletes files that are not monitored

    Parameters:
    dry (bool): If True, performs a dry run without actually deleting files.

    Returns:
    None
    """
    exclude_tags_set = set(config.SONARR.exclude_tags_from_deletion)
    deletions_done = set()
    deletion_ids = set()
    for movie in radarr.get_movie():
        tags_set = set(movie['tags'])
        if bool(tags_set & exclude_tags_set):
            continue
        if movie['monitored'] or not movie['hasFile']:
            continue

        deletions_done.add(movie['title'])
        deletion_ids.add(movie['movieFileId'])

    if not dry and len(deletion_ids) > 0:
        radarr.del_movie_file(list(deletion_ids))

    return list(deletions_done)


def check_if_radarr_is_busy():
    commands = radarr.get_command()
    for command in commands:
        if 'search' in command['name'].lower() and command['status'] != 'completed':
            return True
    return False


def main_run(dry: bool = False):
    # Used in case the arr is managed while updating and there is a difference in length
    global arr_items, config, now_time

    config = ConfigManager().get_config()
    now_time = datetime.datetime.now(datetime.timezone.utc)

    if not config.RADARR.enabled and not dry:
        print("Radarr disabled, doing nothing")
        return
    if check_if_radarr_is_busy() and not dry:
        print("Radarr is busy, doing nothing")
        return

    arr_items = radarr.get_movie()

    quality_changes, _, unmonitor = get_quality_changes()
    monitorable_items, unmonitorable_items = get_monitorable_items()
    deletable_items = get_deletable_items()
    unmonitorable_items += unmonitor
    unmonitorable_items = [item for item in unmonitorable_items if
                           item not in monitorable_items and item.get('monitored', False)]
    monitorable_items = [item for item in monitorable_items if not item.get('monitored', False)]

    if dry:
        print("Finished dry run")
        return {
            "quality_changes": quality_changes,
            "monitorable_items": monitorable_items,
            "unmonitorable_items": unmonitorable_items,
            "deletable_items": deletable_items
        }

    change_quality(quality_changes)
    change_monitoring(monitorable_items, True)
    change_monitoring(unmonitorable_items, False)
    if config.RADARR.delete_unmonitored_files:
        delete_unmonitored_files()
    print("Ran the Radarr instance")


def run(dry: bool = False):
    global radarr
    try:
        radarr = RadarrAPI(config.RADARR.base_url, config.RADARR.api_key)
        return main_run(dry)
    except Exception as error_message:
        pattern_length_difference = r"pyarr\.exceptions\.PyarrServerError: Internal Server Error: Expected query to return (\d+) rows but returned (\d+)"
        match = re.search(pattern_length_difference, error_message)
        if match:
            print("Failed to update Radarr because of difference in length of items")
        print("Radarr failed to update retrying later")
