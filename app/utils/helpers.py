import re


def contains_letters(text: str):
    """Check if a string contains letters"""

    if type(text) is str:
        return re.search(r"[a-zA-Z]", text)


def divide_list_into_chunks(my_list: list, n: int):
    """divide list into chunks"""

    def divide():
        for i in range(0, len(my_list), n):
            yield my_list[i : i + n]

    return list(divide())
