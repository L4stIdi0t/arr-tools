from typing import Any, Dict, List


def _evaluate_numeric_condition(value: float, condition: str) -> bool:
    if '><' in condition:
        min_val, max_val = map(float, condition.split('><'))
        return min_val < value < max_val
    elif '>=' in condition:
        return value >= float(condition[2:])
    elif '<=' in condition:
        return value <= float(condition[2:])
    elif '>' in condition:
        return value > float(condition[1:])
    elif '<' in condition:
        return value < float(condition[1:])
    elif '!=' in condition:
        return value != float(condition[2:])
    elif '==' in condition:
        return value == float(condition[2:])
    return False


def _evaluate_string_condition(value: str, condition: str) -> bool:
    condition = condition.casefold().strip()
    value = value.casefold().strip()

    def parse_condition(condition: str) -> bool:
        if '&&' in condition:
            parts = condition.split('&&')
            return all(parse_condition(part) for part in parts)
        elif '||' in condition:
            parts = condition.split('||')
            return any(parse_condition(part) for part in parts)
        elif '!' in condition:
            part = condition[1:]
            return part not in value
        else:
            return condition in value

    return parse_condition(condition)


def _evaluate_condition(value: Any, condition: str) -> bool:
    if isinstance(value, (int, float)):
        return _evaluate_numeric_condition(float(value), condition)
    elif isinstance(value, str):
        return _evaluate_string_condition(value, condition)
    return False


def _get_value_from_path(item: Dict[str, Any], path: str) -> Any:
    keys = path.split('.')
    for key in keys:
        if key not in item:
            return None
        item = item[key]
    return item


def _process_value(value: Any) -> Any:
    if isinstance(value, list):
        return ' '.join(map(str, value))
    return value


def filter_items(items: List[Dict[str, Any]], filters: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    filtered_items = []

    for item in items:
        match = True
        for filter_criteria in filters:
            for path, condition in filter_criteria.items():
                value = _get_value_from_path(item, path)
                if value is not None:
                    value = _process_value(value)
                if value is None or not _evaluate_condition(value, condition):
                    match = False
                    break
            if not match:
                break
        if match:
            filtered_items.append(item)

    return filtered_items

# Example filters:
# filters = [
#     {"sortTitle": "bill||ted"},
#     {"ratings.imdb.votes": "1000><10000"},
#     {"genres": "Comedy&&Adventure"}
# ]
