function _evaluate_numeric_condition(value, condition) {
  if (condition.includes('><')) {
    const [min_val, max_val] = condition.split('><').map(parseFloat);
    return min_val < value && value < max_val;
  } else if (condition.includes('>=')) {
    return value >= parseFloat(condition.slice(2));
  } else if (condition.includes('<=')) {
    return value <= parseFloat(condition.slice(2));
  } else if (condition.includes('>')) {
    return value > parseFloat(condition.slice(1));
  } else if (condition.includes('<')) {
    return value < parseFloat(condition.slice(1));
  } else if (condition.includes('!=')) {
    return value != parseFloat(condition.slice(2));
  } else if (condition.includes('==')) {
    return value == parseFloat(condition.slice(2));
  }
  return false;
}

function _evaluate_string_condition(value, condition) {
  condition = condition.toLowerCase().trim();
  value = value.toLowerCase().trim();

  function parse_condition(condition) {
    if (condition.includes('&&')) {
      return condition.split('&&').every(parse_condition);
    } else if (condition.includes('||')) {
      return condition.split('||').some(parse_condition);
    } else if (condition.includes('!')) {
      return !value.includes(condition.slice(1));
    } else {
      return value.includes(condition);
    }
  }

  return parse_condition(condition);
}

function _evaluate_condition(value, condition) {
  if (typeof value === 'number') {
    return _evaluate_numeric_condition(value, condition);
  } else if (typeof value === 'string') {
    return _evaluate_string_condition(value, condition);
  }
  return false;
}

function _get_value_from_path(item, path) {
  const keys = path.split('.');
  for (const key of keys) {
    if (!(key in item)) {
      return null;
    }
    item = item[key];
  }
  return item;
}

function _process_value(value) {
  if (Array.isArray(value)) {
    return value.join(' ');
  }
  return value;
}

export function filter_items(items, filters) {
  const filtered_items = [];

  for (const item of items) {
    let match = true;
    for (const filter_criteria of filters) {
      for (const path in filter_criteria) {
        const condition = filter_criteria[path];
        let value = _get_value_from_path(item, path);
        if (value !== null) {
          value = _process_value(value);
        }
        if (value === null || !_evaluate_condition(value, condition)) {
          match = false;
          break;
        }
      }
      if (!match) {
        break;
      }
    }
    if (match) {
      filtered_items.push(item);
    }
  }

  return filtered_items;
}

// Example filters:
// const filters = [
//     {"sortTitle": "bill||ted"},
//     {"ratings.imdb.votes": "1000><10000"},
//     {"genres": "Comedy&&Adventure"}
// ];
