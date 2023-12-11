"""
MIT License

Copyright (c) 2023 White Ribbon Alliance. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

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
import math
import os
import random
import re
from hashlib import sha256

from app import constants
from app.enums.campaign_code import CampaignCode
from app.enums.question_code import QuestionCode
from app.types import CloudService, AzureBlobStorageContainerMountPath


def contains_letters(text: str):
    """Check if a string contains letters"""

    if type(text) is str:
        return re.search(r"[a-zA-Z]", text)


def divide_list_into_chunks_by_text_count(
    my_list: list[str], n: int
) -> list[list[str]]:
    """Divide list into chunks by text count"""

    def divide():
        for i in range(0, len(my_list), n):
            yield my_list[i : i + n]

    return list(divide())


def divide_list_into_chunks_by_char_count(
    my_list: list[str], n: int
) -> list[list[str]]:
    """Divide list into chunks by char count"""

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


def check_campaign(campaign: str) -> CampaignCode:
    """Check if campaign exists"""

    if campaign.lower() in [c.lower() for c in constants.CAMPAIGN_CODES]:
        for campaign_code in CampaignCode:
            if campaign_code.value == campaign:
                return campaign_code


def get_cloud_service_by_campaign(
    campaign_code: CampaignCode,
) -> CloudService:
    """Get translation api code"""

    if campaign_code == CampaignCode.what_young_people_want:
        cloud_service: CloudService = "azure"
    else:
        cloud_service: CloudService = "google"

    return cloud_service


def check_q_code(q_code: str) -> QuestionCode:
    """Check if q code str exists"""

    for q in QuestionCode:
        if q.value == q_code:
            return q


def clear_tmp_dir():
    """Clear tmp dir"""

    if not os.path.isdir("/tmp"):
        return

    for filename in glob.glob("/tmp/wra_*"):
        try:
            os.remove(filename)
        except OSError:
            pass


def get_distributed_list_of_dictionaries(
    data_lists: list[list[dict]],
    sort_by_key: str = None,
    remove_duplicates: bool = False,
    n_items: int = None,
    skip_list_size_check: bool = False,
    shuffle: bool = False,
) -> list[dict]:
    """
    Given a list containing a list of dictionaries, distribute the list items to a single list of dictionaries.

    :param data_lists: A list containing lists of dictionaries.
    :param sort_by_key: Optional, sort by dictionary key (desc) and pick top items.
    :param remove_duplicates: Optional, remove duplicates from list.
    :param n_items: Optional, n items to pick from each list.
    :param skip_list_size_check: Optional, skip checking the size of returned list.
    :param shuffle: Optional, shuffle result.
    """

    distributed_data_list = []

    # Get items count of list with most items
    items_counts_list = [len(data_list) for data_list in data_lists]
    if len(items_counts_list) > 0:
        max_items_count = max(items_counts_list)
    else:
        max_items_count = 0

    # Get items from each list
    for data_list in data_lists:
        if data_list:
            # n items
            if not n_items:
                n_items = math.ceil(max_items_count / len(data_lists))
            if n_items > len(data_list):
                n_items = len(data_list)

            # Sort list by dict key and pick the top n results
            if sort_by_key:
                data_list_sorted = sorted(
                    data_list, key=lambda d: d.get(sort_by_key), reverse=True
                )
                distributed_data_list.extend(data_list_sorted[:n_items])

            # Pick random n sample
            else:
                distributed_data_list.extend(
                    random.sample(population=data_list, k=n_items)
                )

    # Remove duplicates
    if remove_duplicates:
        distributed_data_list = [
            x
            for index, x in enumerate(distributed_data_list)
            if x not in distributed_data_list[:index]
        ]

    # Keep the list the size of max_items_count
    if not skip_list_size_check:
        if len(distributed_data_list) > max_items_count:
            distributed_data_list = distributed_data_list[:max_items_count]

    # Shuffle
    if shuffle:
        random.shuffle(distributed_data_list)

    return distributed_data_list


def get_unique_flattened_list_of_dictionaries(
    data_lists: list[list[dict]],
) -> list[dict]:
    """
    Given a list containing a list of dictionaries, flatten the list and remove duplicates.

    :param data_lists: A list containing lists of dictionaries.
    """

    # Flatten the list
    data_lists_flattened: list[dict] = []
    for data_list in data_lists:
        data_lists_flattened.extend([x for x in data_list if x])

    # Remove duplicate dictionaries from list
    data_lists_flattened = [
        x
        for index, x in enumerate(data_lists_flattened)
        if x not in data_lists_flattened[:index]
    ]

    return data_lists_flattened


def get_merged_flattened_list_of_dictionaries(
    data_lists: list[list[dict]], unique_key: str, keys_to_merge: list[str]
) -> list[dict]:
    """
    Given a list containing a list of dictionaries, find duplicates by a specific dictionary key and merge them to a
    single list.

    :param data_lists: A list containing lists of dictionaries.
    :param unique_key: Key to use for checking duplicates.
    :param keys_to_merge: If the value of the key is an int, add the value to an existing dictionary with same key.
    """

    # Flatten the list
    data_lists_flattened: list[dict] = []
    for data_lists in data_lists:
        data_lists_flattened.extend([x for x in data_lists if x])

    tmp_merged: dict[str, dict] = {}
    for data in data_lists_flattened:
        data_key_value = data.get(unique_key)
        if not data_key_value:
            continue

        # Add data to dict
        if data_key_value not in tmp_merged.keys():
            tmp_merged[data_key_value] = data

        # Merge data to existing dict in list
        else:
            for key_to_merge in keys_to_merge:
                if isinstance(
                    tmp_merged.get(data_key_value, {}).get(key_to_merge), int
                ) and isinstance(data.get(key_to_merge, {}), int):
                    tmp_merged[data_key_value][key_to_merge] += data[key_to_merge]

    merged_list = [v for v in tmp_merged.values()]

    return merged_list


def extract_first_occurring_numbers(
    value: str, first_less_than_symbol_to_0: bool = False
) -> int:
    """
    Extract numbers until the next char is not numeric e.g. "25-30" -> 25.
    Optionally use "0" in place of the first value if it is "<".
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
        return 0

    return int("".join(numbers))


def get_dict_hash_value(dictionary: dict[str, any]) -> str:
    """Get dictionary hash value"""

    md5_hash = hashlib.md5()
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    md5_hash.update(encoded)

    return md5_hash.hexdigest()


def get_string_hash_value(string: str) -> str:
    """Get string hash value"""

    return sha256(string.encode()).hexdigest()


def get_translation_languages(cloud_service: CloudService) -> dict:
    """Get translation languages"""

    # Languages supported by Cloud Translation API
    if cloud_service == "google":
        return constants.LANGUAGES_GOOGLE
    elif cloud_service == "azure":
        return constants.LANGUAGES_AZURE

    return {}


def create_tmp_dir_if_not_exists():
    """Create '/tmp' dir"""

    tmp_dir_path = "/tmp"
    if not os.path.isdir(tmp_dir_path):
        os.mkdir(tmp_dir_path)


def create_pmnch_main_dir_if_not_exists():
    """
    Create '/pmnch_main' dir.
    Is a path mapping to an Azure Blob storage container.
    """

    container_mount_path: AzureBlobStorageContainerMountPath = "/pmnch_main"
    if not os.path.isdir(container_mount_path):
        os.mkdir(container_mount_path)


def create_pmnch_csv_dir_if_not_exists():
    """
    Create '/pmnch_csv' dir.
    Is a path mapping to an Azure Blob storage container.
    """

    container_mount_path: AzureBlobStorageContainerMountPath = "/pmnch_csv"
    if not os.path.isdir(container_mount_path):
        os.mkdir(container_mount_path)
