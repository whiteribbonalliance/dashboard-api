"""
MIT License

Copyright (c) 2023 World We Want. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import glob
import hashlib
import json
import os
import re
from hashlib import sha256

from app import constants
from app.helpers import q_col_names


def contains_letters(text: str):
    """
    Check if a string contains letters.
    """

    if type(text) is str:
        return re.search(r"[a-zA-Z]", text)


def divide_list_into_chunks_by_text_count(
    my_list: list[str], n: int
) -> list[list[str]]:
    """
    Divide list into chunks by text count.
    """

    def divide():
        for i in range(0, len(my_list), n):
            yield my_list[i : i + n]

    return list(divide())


def divide_list_into_chunks_by_char_count(
    my_list: list[str], n: int
) -> list[list[str]]:
    """
    Divide list into chunks by char count.
    """

    total_chars_count = sum(len(i) for i in my_list)
    if total_chars_count <= n:
        return [my_list]

    result_list = []
    tmp_list = []
    char_count = 0
    for index, text in enumerate(my_list):
        char_count += len(text)
        if char_count <= n:
            tmp_list.append(text)
        else:
            result_list.append(tmp_list)
            char_count = len(text)
            tmp_list = [text]
        if index + 1 == len(my_list):
            result_list.append(tmp_list)

    return result_list


def clear_tmp_dir():
    """
    Clear tmp dir.
    """

    if not os.path.isdir("/tmp"):
        return

    for filename in glob.glob("/tmp/export_*"):
        try:
            os.remove(filename)
        except OSError:
            pass


def extract_first_occurring_numbers(
    value: str, first_less_than_symbol_to_0: bool = False
) -> int:
    """
    Extract numbers until the next char is not numeric e.g. "25-30" -> 25.
    Optionally use "0" in place of the first value if it is "<" to include it as a number.
    """

    numbers = []
    for i, c in enumerate(value):
        if first_less_than_symbol_to_0 and i == 0 and c == "<":
            numbers.append("0")
        elif c.isdigit():
            numbers.append(c)
        else:
            if len(numbers) > 0:
                break

    if not numbers:
        return -1

    return int("".join(numbers))


def get_dict_hash_value(dictionary: dict[str, any]) -> str:
    """
    Get dictionary hash value.
    """

    md5_hash = hashlib.md5()
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    md5_hash.update(encoded)

    return md5_hash.hexdigest()


def get_string_hash_value(string: str) -> str:
    """
    Get string hash value.
    """

    return sha256(string.encode()).hexdigest()


def get_translation_languages(cloud_service: str) -> dict:
    """
    Get translation languages.
    """

    if cloud_service == "google":
        return constants.LANGUAGES_GOOGLE
    elif cloud_service == "azure":
        return constants.LANGUAGES_AZURE

    return {}


def create_tmp_dir_if_not_exists():
    """
    Create /tmp dir.
    """

    tmp_dir_path = "/tmp"
    if not os.path.isdir(tmp_dir_path):
        os.mkdir(tmp_dir_path)


def get_required_columns(q_codes: list[str]) -> list[str]:
    """
    Get required columns.
    """

    columns = ["alpha2country", "age"]
    for q_code in q_codes:
        columns.append(q_col_names.get_response_col_name(q_code=q_code))
        columns.append(q_col_names.get_canonical_code_col_name(q_code=q_code))
        columns.append(q_col_names.get_lemmatized_col_name(q_code=q_code))

    return columns
