import editdistance
from unidecode import unidecode


def normalize_string(input_str: str, remove_case: bool = True) -> str:
    """
    Normalize the input string by removing emojis and replacing complicated characters with simpler versions.

    Args:
        remove_case: If it should remove the case of the string.
        input_str (str): The string to normalize.

    Returns:
        str: The normalized string.
    """
    normalized = unidecode(input_str).strip()
    if remove_case:
        normalized = normalized.casefold()
    return normalized


def fuzzy_str_match(query, target, max_changes_per_word=1, normalize_words=True):
    """
    Check if two strings are fuzzy matches, allowing a maximum number of changes per word.

    Args:
        query (str): The query string to match.
        target (str): The target string to match against.
        max_changes_per_word (int, optional): The maximum number of changes allowed per word.
            Defaults to 1.
        normalize_words: Makes the string normalize words.

    Returns:
        bool: True if the strings are fuzzy matches within the specified maximum changes per word, False otherwise.
    """
    if normalize_words:
        query = normalize_string(query, remove_case=True)
        target = normalize_string(target, remove_case=True)

    query_words = query.split()
    target_words = target.split()

    if len(query_words) != len(target_words):
        return False

    for q_word, t_word in zip(query_words, target_words):
        if editdistance.eval(q_word, t_word) > max_changes_per_word:
            return False

    return True
