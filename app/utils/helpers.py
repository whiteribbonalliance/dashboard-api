import re


def contains_letters(text: str):
    """Check if a string contains letters"""

    if type(text) is str:
        return re.search(r"[a-zA-Z]", text)
