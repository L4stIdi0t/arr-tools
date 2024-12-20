import datetime
import re
import time
from collections import defaultdict

from sqlalchemy.orm import Session

from database.database import get_program_db
from utils.config_manager import ConfigManager
from utils.customSonarApi import customSonarAPI
from utils.general_arr_actions import reassign_based_on_age, link_arr_to_media_server, \
    classify_items_by_decay, combine_tuples, sort_tuples, subtract_dicts
from utils.media_server_interaction import MediaServerinteracter
from utils.process_filter import filter_items

# TODO: Optimize media server api calls, cache results...

config = ConfigManager().get_config()

media_server = MediaServerinteracter(config.MEDIASERVER.media_server_type, config.MEDIASERVER.media_server_base_url,
                                     config.MEDIASERVER.media_server_api_key)
sonarr = None
arr_items = []
now_time = datetime.datetime.now(datetime.timezone.utc)

db: Session = next(get_program_db())

rechecked_history = {}


def get_quality_changes():
    quality_items = []
    unmonitor = []

    watched_items = []
    favorited_items = []

    if config.SONARR.use_favorite:
        favorited_items = \
            media_server.get_all_favorites(ignore_user_ids=config.SONARR.exclude_users_from_quality_upgrades)["Series"]
    if config.SONARR.use_watched:
        watched_items = \
            media_server.get_played(ignore_user_ids=config.SONARR.exclude_users_from_quality_upgrades)["Series"]
        played_items = media_server.get_played(ignore_user_ids=config.SONARR.exclude_users_from_monitoring)
        watched_items = played_items["Series"] + played_items["Episodes"] + watched_items
        temp = {item['Name'] for item in watched_items}
        watched_items = [{'Name': item} for item in temp]

    # Convert media server format to arr format
    watched_items = [
        arr_item for item in watched_items
        if (arr_item := link_arr_to_media_server(item, arr_items)) is not None
    ]
    favorited_items = [
        arr_item for item in favorited_items
        if (arr_item := link_arr_to_media_server(item, arr_items)) is not None
    ]

    quality_items += classify_items_by_decay(items=watched_items, decay_days=config.SONARR.watched_decay_days,
                                             decay_start_timer=config.SONARR.decay_start_timer,
                                             played_items=watched_items,
                                             quality_profile=config.SONARR.watched_quality_profile)
    quality_items += classify_items_by_decay(favorited_items, config.SONARR.favorite_decay_days,
                                             config.SONARR.decay_start_timer, favorited_items,
                                             config.SONARR.favorited_quality_profile)

    # region Filters
    filters = config.SONARR.popular_filters
    very_popular_items = filter_items(arr_items, filters["very_popular"])
    popular_items = filter_items(arr_items, filters["popular"])
    less_popular_items = filter_items(arr_items, filters["less_popular"])
    unpopular_items = filter_items(arr_items, filters["unpopular"])
    reassign_based_on_age(very_popular_items, config.SONARR.very_popular_decay_days, config.SONARR.decay_start_timer,
                          watched_items, very_popular_items, popular_items)
    reassign_based_on_age(popular_items, config.SONARR.popular_decay_days, config.SONARR.decay_start_timer,
                          watched_items, popular_items, less_popular_items)
    reassign_based_on_age(less_popular_items, config.SONARR.less_popular_decay_days, config.SONARR.decay_start_timer,
                          watched_items, less_popular_items,
                          unpopular_items)
    reassign_based_on_age(unpopular_items, config.SONARR.unpopular_decay_days, config.SONARR.decay_start_timer,
                          watched_items, unpopular_items, unmonitor)

    quality_items.append((config.SONARR.very_popular_quality_profile, very_popular_items))
    quality_items.append((config.SONARR.popular_quality_profile, popular_items))
    quality_items.append((config.SONARR.less_popular_quality_profile, less_popular_items))
    quality_items.append((config.SONARR.unpopular_quality_profile, unpopular_items))
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
            quality_id = config.SONARR.low_quality_profile
        elif tuple[0] == 1:
            quality_id = config.SONARR.normal_quality_profile
        elif tuple[0] == 2:
            quality_id = config.SONARR.high_quality_profile
        elif tuple[0] == 3:
            quality_id = config.SONARR.ultra_quality_profile

        if quality_id is None:
            print(f"Configuration for {tuple[0]} quality id is bad")
            continue

        for item in tuple[1]:
            if not item:
                continue
            if not 'qualityProfileId' in item:
                print(f"Item {item} has no quality profile id")
            if item['qualityProfileId'] != quality_id:
                quality_changes.append({'item': item, 'new_quality_profile': quality_id})
            else:
                monitor_items.append(item)

    return quality_changes, monitor_items, unmonitor_items


def _monitor_episodes_ahead(episodes, season_number, episode_number, ahead_count, series):
    episode_ids = []
    count = 0
    ahead_count += 1
    episodes = sorted(episodes, key=lambda ep: (ep['seasonNumber'], ep['episodeNumber']))
    for episode in episodes:
        if season_number == episode['seasonNumber'] and episode_number == episode['episodeNumber'] and count == 0:
            count += 1

        if count <= ahead_count and count != 0:
            count += 1
            episode_ids.append({
                'episode_id': episode['id'],
                'series_id': series['id'],
                'monitored': episode['monitored'],
                'season_number': episode['seasonNumber'],
                'tags': series['tags']
            })

        if count > ahead_count:
            continue
    return episode_ids


def _monitor_episodes_behind(episodes, season_number, episode_number, ahead_count, series):
    episode_ids = []
    count = 0
    ahead_count += 1
    episodes = sorted(episodes, key=lambda ep: (ep['seasonNumber'], ep['episodeNumber']))
    episodes.reverse()

    for episode in episodes:
        if season_number == episode['seasonNumber'] and episode_number == episode['episodeNumber'] and count == 0:
            count += 1

        if count <= ahead_count and count != 0 and episode['seasonNumber'] != 0:
            count += 1
            episode_ids.append({
                'episode_id': episode['id'],
                'series_id': series['id'],
                'monitored': episode['monitored'],
                'season_number': episode['seasonNumber'],
                'tags': series['tags']
            })

        if count > ahead_count:
            continue
    return episode_ids


def get_monitorable_items():
    favorited_items = []
    unmonitor_episodes = []
    very_popular_items = []
    popular_items = []
    less_popular_items = []
    unpopular_items = []
    unmonitor = []

    exclude_tags_set = set(config.SONARR.exclude_tags_from_monitoring)

    # region Monitor & unmonitor series
    if config.SONARR.use_favorite and config.SONARR.mark_favorited_as_monitored:
        favorited_items = \
            media_server.get_all_favorites(ignore_user_ids=config.SONARR.exclude_users_from_monitoring)["Series"]
    played_items = media_server.get_played(ignore_user_ids=config.SONARR.exclude_users_from_monitoring)
    played_series = played_items["Series"] + played_items["Episodes"]
    temp = {item['Name'] for item in played_series}
    played_series = [{'Name': item} for item in temp]

    favorited_items = [
        arr_item for item in favorited_items
        if (arr_item := link_arr_to_media_server(item, arr_items)) is not None
    ]
    played_series = [
        arr_item for item in played_series
        if (arr_item := link_arr_to_media_server(item, arr_items)) is not None
    ]

    filters = config.SONARR.popular_filters
    if config.SONARR.mark_very_popular_as_monitored:
        very_popular_items = filter_items(arr_items, filters["very_popular"])
    if config.SONARR.mark_popular_as_monitored:
        popular_items = filter_items(arr_items, filters["popular"])
    if config.SONARR.mark_less_popular_as_monitored:
        less_popular_items = filter_items(arr_items, filters["less_popular"])
    if config.SONARR.mark_unpopular_as_monitored or config.SONARR.mark_unpopular_as_unmonitored:
        unpopular_items = filter_items(arr_items, filters["unpopular"])
    reassign_based_on_age(very_popular_items, config.SONARR.very_popular_decay_days, config.SONARR.decay_start_timer,
                          played_series, very_popular_items, popular_items)
    reassign_based_on_age(popular_items, config.SONARR.popular_decay_days, config.SONARR.decay_start_timer,
                          played_series, popular_items, less_popular_items)
    reassign_based_on_age(less_popular_items, config.SONARR.less_popular_decay_days, config.SONARR.decay_start_timer,
                          played_series, less_popular_items,
                          unpopular_items)
    reassign_based_on_age(unpopular_items, config.SONARR.unpopular_decay_days, config.SONARR.decay_start_timer,
                          played_series, unpopular_items, unmonitor)

    monitor = favorited_items + played_series + very_popular_items + popular_items + less_popular_items

    if config.SONARR.mark_unpopular_as_monitored:
        monitor += unpopular_items
    if config.SONARR.mark_unpopular_as_unmonitored:
        unmonitor += unpopular_items

    temp = []
    for item in monitor:
        item_tags = set(item['tags'])
        if bool(item_tags & exclude_tags_set):
            continue
        temp.append(item)
    monitor = temp
    temp = []
    for item in unmonitor:
        item_tags = set(item['tags'])
        if bool(item_tags & exclude_tags_set):
            continue
        temp.append(item)
    unmonitor = temp
    # endregion

    # region Monitor episodes based on users watched episodes
    recheck_releases = []
    max_played_episodes = []
    max_played_episodes_shows = []
    for item in media_server.get_max_played_episodes():
        arr_item = link_arr_to_media_server(item, arr_items)
        if not arr_item:
            continue
        max_played_episodes.append(item)
        max_played_episodes_shows.append(arr_item)

    monitor_episodes = []
    for idx in range(len(max_played_episodes)):
        if not max_played_episodes_shows[idx]:
            continue
        tags_set = set(max_played_episodes_shows[idx]['tags'])
        if bool(exclude_tags_set & tags_set):
            continue

        series_id = max_played_episodes_shows[idx]["id"]
        episodes_data = sonarr.get_episode(series_id, series=True)

        for episode in episodes_data:
            airdate = now_time
            airdate_str = episode.get('airDateUtc', None)
            if airdate_str:
                airdate = datetime.datetime.strptime(airdate_str,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
            if not episode.get('hasFile', True) and episode.get('monitored', False) and airdate < now_time:
                recheck_releases.append(series_id)
                break

        max_episode_data = defaultdict(int)
        if config.SONARR.base_monitoring_amount == 0:
            for episode in episodes_data:
                max_episode_data[episode['seasonNumber']] = max(max_episode_data[episode['seasonNumber']],
                                                                episode['episodeNumber'])

        for episode in episodes_data:
            episode_id = episode['id']
            monitoring_item = {
                'episode_id': episode_id,
                'series_id': series_id,
                'season_number': episode['seasonNumber'],
                'tags': max_played_episodes_shows[idx]['tags'],
                'monitored': episode['monitored']
            }

            if config.SONARR.monitoring_amount == 0 and any(
                    episode['seasonNumber'] == max_episode['Season'] for max_episode in
                    max_played_episodes[idx]["Episodes"]):
                monitor_episodes.append(monitoring_item)
            # A big mess which i am too lazy to clean but should work just fine
            elif config.SONARR.monitoring_amount == 0:
                for max_episode in max_played_episodes[idx]["Episodes"]:
                    if max_episode['Season'] == episode['seasonNumber']:
                        if max_episode_data[max_episode['Season']] - max_episode['Episode'] <= 3:
                            for episode in episodes_data:
                                if any(episode['seasonNumber'] + 1 == max_episode['Season'] for max_episode in
                                       max_played_episodes[idx]["Episodes"]):
                                    monitor_episodes.append(monitoring_item)
            elif config.SONARR.monitoring_amount == 3:
                monitor_episodes.append(monitoring_item)
            else:
                for max_episode in max_played_episodes[idx]["Episodes"]:
                    if config.SONARR.monitoring_amount == 1:
                        monitor_episodes += \
                            _monitor_episodes_ahead(episodes_data, max_episode['Season'], max_episode["Episode"], 3,
                                                    max_played_episodes_shows[idx])
                        monitor_episodes += \
                            _monitor_episodes_behind(episodes_data, max_episode['Season'], max_episode["Episode"], 3,
                                                     max_played_episodes_shows[idx])
                    elif config.SONARR.monitoring_amount == 2:
                        monitor_episodes += \
                            _monitor_episodes_ahead(episodes_data, max_episode['Season'], max_episode["Episode"], 6,
                                                    max_played_episodes_shows[idx])
                        monitor_episodes += \
                            _monitor_episodes_behind(episodes_data, max_episode['Season'], max_episode["Episode"], 6,
                                                     max_played_episodes_shows[idx])

    temp = (item['series_id'] for item in monitor_episodes)
    for index, item in enumerate(recheck_releases):
        if item in temp:
            recheck_releases.pop(index)
    # endregion

    # region Monitor base amount and create unmonitor episodes
    for arr_item in arr_items:
        tags_set = set(arr_item['tags'])
        if bool(exclude_tags_set & tags_set):
            continue

        series_id = arr_item["id"]
        episodes_data = sonarr.get_episode(series_id, series=True)

        for episode in episodes_data:
            episode_id = episode['id']

            monitoring_item = {
                'episode_id': episode_id,
                'series_id': series_id,
                'season_number': episode['seasonNumber'],
                'tags': arr_item['tags'],
                'monitored': episode['monitored']
            }

            unmonitor_episodes.append(monitoring_item)

            if episode["seasonNumber"] != 1 and config.SONARR.base_monitoring_amount != 3:
                continue

            if config.SONARR.base_monitoring_amount == 0 or config.SONARR.base_monitoring_amount == 3 or (
                    config.SONARR.base_monitoring_amount == 1 and episode["episodeNumber"] <= 3) or (
                    config.SONARR.base_monitoring_amount == 2 and episode["episodeNumber"] <= 6):
                monitor_episodes.append(monitoring_item)

    monitored_ids = [item['episode_id'] for item in monitor_episodes]
    unmonitor_episodes = [episode for episode in unmonitor_episodes if episode['episode_id'] not in monitored_ids]
    # endregion

    return monitor, unmonitor, monitor_episodes, unmonitor_episodes, recheck_releases


def get_deletable_items():
    pass


def change_quality(quality_changes):
    def check_if_quality_exists(quality_id):
        qualities = sonarr.get_quality_profile()
        for quality in qualities:
            if quality["id"] == quality_id:
                return True
        return False

    changed_dict = {}
    for quality_change in quality_changes:
        if bool(set(quality_change['item']['tags']) & set(config.SONARR.exclude_tags_from_quality_upgrades)):
            continue

        if quality_change['new_quality_profile'] not in changed_dict:
            changed_dict[quality_change['new_quality_profile']] = set()
        changed_dict[quality_change['new_quality_profile']].add(quality_change['item']['id'])

    if config.SONARR.monitor_quality_changes:
        monitor = set()
        for quality_change in quality_changes:
            item = quality_change['item']
            if bool(set(item['tags']) & set(config.SONARR.exclude_tags_from_monitoring)):
                continue

            monitor.add(item['id'])

        sonarr.upd_series_editor({"monitored": True, "seriesIds": list(monitor)})

    changed_list = [
        {"qualityProfileId": quality, "seriesIds": list(ids)}
        for quality, ids in changed_dict.items()
    ]

    for changes in changed_list:
        if not check_if_quality_exists(changes['qualityProfileId']):
            continue

        sonarr.upd_series_editor(changes)

        if config.SONARR.search_for_quality_upgrades:
            for serieId in changes['seriesIds']:
                sonarr.post_command("SeriesSearch", seriesId=serieId)


def delete_unmonitored_files(dry: bool = False, delete: list = ['episode']):
    """
    Deletes files that are not monitored based on specified criteria.

    Parameters:
    dry (bool): If True, performs a dry run without actually deleting files.
    delete (list): List of types to be deleted. Only episodes enabled

    Returns:
    None
    """
    for type in delete:
        if type != 'episode':
            raise NotImplemented('Only episode type is currently supported')

    exclude_tags_set = set(config.SONARR.exclude_tags_from_deletion)
    deletions_done = set()
    for serie in sonarr.get_series():
        tags_set = set(serie['tags'])
        if bool(tags_set & exclude_tags_set):
            continue
        if 'episode' in delete:
            episodes = sonarr.get_episode(serie['id'], series=True)
            for episode in episodes:
                if episode['monitored'] or not episode['hasFile']:
                    continue
                deletions_done.add(f'{serie["title"]} | S{episode["seasonNumber"]}E{episode["episodeNumber"]}')
                if dry:
                    continue
                sonarr.del_episode_file(episode['episodeFileId'])
        else:
            pass
            # To extend here..

    return list(deletions_done)


def change_monitoring(monitoring_changes: list, monitor: bool):
    allowed_changes = set()
    exclude_tags_set = set(config.SONARR.exclude_tags_from_monitoring)
    for item in monitoring_changes:
        tags_set = set(item['tags'])
        if bool(tags_set & exclude_tags_set):
            continue
        allowed_changes.add(item['id'])

    sonarr.upd_series_editor({"monitored": monitor, "seriesIds": list(allowed_changes)})

    if monitor:
        for _id in allowed_changes:
            sonarr.post_command("SeriesSearch", seriesId=_id)


def change_monitoring_episodes(monitoring_changes: list, monitor: bool):
    exclude_tags_set = set(config.SONARR.exclude_tags_from_monitoring)
    if monitor:
        seasons_monitoring = defaultdict(set)
        for item in monitoring_changes:
            tags_set = set(item['tags'])
            if bool(tags_set & exclude_tags_set):
                continue

            seasons_monitoring[item['series_id']].add(item['season_number'])
        for serie_id, seasons in seasons_monitoring.items():
            found_series = next((item for item in arr_items if item['id'] == serie_id), None)
            changed_season = False
            for season in found_series['seasons']:
                if season['monitored']:
                    continue
                if season['seasonNumber'] in seasons:
                    season['monitored'] = True
                    changed_season = True

            if changed_season:
                sonarr.upd_series(found_series)

    allowed_changes = set()
    search_series = set()
    for item in monitoring_changes:
        tags_set = set(item['tags'])
        if bool(tags_set & exclude_tags_set):
            continue
        if item['monitored'] == monitor:
            continue
        allowed_changes.add(item['episode_id'])
        search_series.add(item['series_id'])

    sonarr.upd_episode_monitor(list(allowed_changes), monitor)

    if monitor:
        for _id in search_series:
            sonarr.post_command("SeriesSearch", seriesId=_id)


def search_series(series_id: int):
    sonarr.post_command("SeriesSearch", seriesId=series_id)


def check_if_sonarr_is_busy():
    commands = sonarr.get_command()
    for command in commands:
        if 'search' in command['name'].lower() and command['status'] != 'completed':
            return True
    return False


def main_run(dry: bool = False):
    # Used in case the arr is managed while updating and there is a difference in length
    global arr_items, config, now_time, rechecked_history

    config = ConfigManager().get_config()
    now_time = datetime.datetime.now(datetime.timezone.utc)

    if not config.SONARR.enabled and not dry:
        print("Sonarr disabled, doing nothing")
        return
    if check_if_sonarr_is_busy() and not dry:
        print("Sonarr is busy, doing nothing")
        return

    arr_items = sonarr.get_series()

    quality_changes, monitor, unmonitor = get_quality_changes()
    monitorable_items, unmonitorable_items, monitor_episodes, unmonitor_episodes, recheck_releases = get_monitorable_items()
    deletable_items = get_deletable_items()
    monitorable_items += monitor
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
            "monitorable_episodes": monitor_episodes,
            "unmonitorable_episodes": unmonitor_episodes,
            "deletable_items": deletable_items
        }

    change_quality(quality_changes)
    change_monitoring(monitorable_items, True)
    change_monitoring(unmonitorable_items, False)
    change_monitoring_episodes(monitor_episodes, True)
    change_monitoring_episodes(unmonitor_episodes, False)
    if config.SONARR.delete_unmonitored_files:
        delete_unmonitored_files()

    final_recheck_releases = []
    for item in set(recheck_releases):
        now_time = time.time()
        if item not in rechecked_history:
            final_recheck_releases.append(item)
            rechecked_history[item] = [now_time]
            continue

        checked_times = rechecked_history[item]
        if checked_times[0] + 3600 < now_time:
            del rechecked_history[item][0]
        if len(checked_times) >= 3:
            continue

        final_recheck_releases.append(item)
        rechecked_history[item].append(now_time)

    for item in final_recheck_releases:
        search_series(item)

    print("Ran the Sonarr instance")


def run(dry: bool = False):
    global sonarr
    try:
        sonarr = customSonarAPI(config.SONARR.base_url, config.SONARR.api_key)
        return main_run(dry)
    except Exception as error_message:
        pattern_length_difference = r"pyarr\.exceptions\.PyarrServerError: Internal Server Error: Expected query to return (\d+) rows but returned (\d+)"
        match = re.search(pattern_length_difference, error_message)
        if match:
            print("Failed to update Sonarr because of difference in length of items")
        print("Sonarr failed to update retrying later")
