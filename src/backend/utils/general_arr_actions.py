import datetime

from collections import defaultdict
from typing import List, Tuple, Dict


def get_start_time(item: dict, decay_start_timer: int, played_items=None) -> datetime.datetime:
    """Retrieve the start time of an item based on the decay_start_timer configuration.

    Args:
        item (dict): The item dictionary containing the start time information.
        decay_start_timer (int): Specifies how to decay the start time.

    Returns:
        datetime: The start time of the item as a timezone-aware datetime object.
    """
    utc_now = datetime.datetime.now(datetime.timezone.utc)

    def get_shortest_time():
        # Convert strings to datetime objects, default to a very old date if not available
        added = datetime.datetime.strptime(item.get('added', '1000-01-01T00:00:00Z'), "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc)
        last_aired = datetime.datetime.strptime(item.get('lastAired', '1000-01-01T00:00:00Z'),
                                                "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc)
        in_cinemas = datetime.datetime.strptime(item.get('inCinemas', '1000-01-01T00:00:00Z'),
                                                "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc)
        digital_release = datetime.datetime.strptime(item.get('digitalRelease', '1000-01-01T00:00:00Z'),
                                                     "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc)

        # Calculate differences from utc_now
        time_diffs = [
            (abs(utc_now - added), added),
            (abs(utc_now - last_aired), last_aired),
            (abs(utc_now - in_cinemas), in_cinemas),
            (abs(utc_now - digital_release), digital_release)
        ]

        # Find the closest time
        closest_time = min(time_diffs, key=lambda x: x[0])[1]
        return closest_time

    try:
        if decay_start_timer == 0:
            return datetime.datetime.strptime(item.get('added', '0000-01-01T00:00:00Z'), "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=datetime.timezone.utc)
        elif decay_start_timer == 1:
            return get_shortest_time()
        elif not played_items:
            print("You should add played items to the function call")
            return get_shortest_time()
        elif decay_start_timer == 2:
            for played in played_items:
                if played["name"] == item["title"]:
                    return played['date']
            return datetime.datetime.strptime(item.get('added', '0000-01-01T00:00:00Z'), "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=datetime.timezone.utc)
        elif decay_start_timer == 3:
            for played in played_items:
                if played["name"] == item["title"]:
                    return played['date']
            return get_shortest_time()

    except KeyError:
        return utc_now


def reassign_based_on_age(items, decay_days, decay_start_timer, played_items, source_list, target_list=None) -> None:
    """Reassigns items to a different list based on their age relative to a specified decay period.

    This function iterates over the given items, calculates their age using the get_start_time function,
    and compares it to the current date minus the specified decay days. If an item's age exceeds the
    decay period, it is removed from the source list. If a target list is provided, the item is appended
    to the target list.

    Args:
        items (list): The list of items to be checked and potentially reassigned.
        decay_days (int): The number of days representing the decay period.
        source_list (list): The list from which items are removed if they exceed the decay period.
        target_list (list, optional): The list to which items are appended if they exceed the decay period.
                                      Defaults to None, in which case items are simply removed from the source list.
    """
    threshold_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=decay_days)
    for item in list(items):
        start_time = get_start_time(item, decay_start_timer, played_items)
        if start_time < threshold_date:
            source_list.remove(item)
            if target_list is not None:
                target_list.append(item)


def classify_items_by_decay(items: List[dict], decay_days: int, decay_start_timer: int, played_items: list,
                            quality_profile: int) -> List[
    Tuple[int, List[dict]]]:
    return [(quality_profile, items)]

    decay_profiles = {}

    for item in items:
        start_time = get_start_time(item=item, decay_start_timer=decay_start_timer, played_items=played_items)
        age_days = (now_time - start_time).days

        if age_days >= decay_days:
            profile_level = max(1, quality_profile - (age_days // decay_days))

            if profile_level not in decay_profiles:
                decay_profiles[profile_level] = []

            decay_profiles[profile_level].append(item)

    result = [(profile, decay_profiles[profile]) for profile in sorted(decay_profiles.keys(), reverse=True)]
    return result


def link_arr_to_media_server(media_server_item: dict, arr_items: list) -> dict:
    """
    Link an item from a media server to a corresponding item in a list.

    Args:
        media_server_item (dict): A dictionary containing information about the media server item, including 'Name'.
        arr_items (list): A list of dictionaries, each containing 'title' and 'year' information.

    Returns:
        dict: The matched dictionary from arr_items if a match is found, otherwise None.
    """
    import re

    original_title = media_server_item['Name'].casefold()
    title = re.sub(r'\s*\(\d{4}\)$', '', original_title)  # Remove (year) from the title
    year_match = re.search(r'\((\d{4})\)$', original_title)
    year = int(year_match.group(1)) if year_match and 1900 <= int(year_match.group(1)) <= 2200 else None

    for arr_item in arr_items:
        arr_title = arr_item['title'].casefold()
        arr_year = arr_item.get('year')
        if arr_title == original_title or (title == arr_title and year == arr_year):
            return arr_item

def combine_tuples(tuples: List[Tuple[int, List[int]]]) -> List[Tuple[int, List[int]]]:
    combined_dict = defaultdict(list)

    for key, value in tuples:
        combined_dict[key].extend(value)

    return [(key, combined_dict[key]) for key in sorted(combined_dict)]


def sort_tuples(tuples: List[Tuple[int, List[int]]], reverse: bool = True) -> List[Tuple[int, List[int]]]:
    return sorted(tuples, key=lambda x: x[0], reverse=reverse)


def subtract_dicts(tuples: List[Tuple[int, List[Dict]]]) -> List[Tuple[int, List[Dict]]]:
    previous_elements = []

    for i in range(len(tuples)):
        current_elements = tuples[i][1]
        new_elements = [item for item in current_elements if item not in previous_elements]
        tuples[i] = (tuples[i][0], new_elements)
        previous_elements.extend(current_elements)

    return tuples


def check_ids(ids: list, items: List[Dict]):
    unique_ids = set()
    for item in items:
        unique_ids.add(item['id'])

    available_ids = []
    unavailable_ids = []
    for _id in ids:
        if _id in unique_ids:
            available_ids.append(_id)
        else:
            unavailable_ids.append(_id)
    return available_ids, unavailable_ids
