import re


def make_filename_safe(input_string):
    """Convert input string to a filename-safe string."""
    # Remove any characters that are not alphanumeric, hyphens, underscores, periods, or spaces
    return re.sub(r"[^a-zA-Z0-9._\- ]", "", input_string)
