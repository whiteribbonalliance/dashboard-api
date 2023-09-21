import glob
import math
import os
import random
import re

from app import constants
from app.enums.campaign_code import CampaignCode
from app.enums.question_code import QuestionCode


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


def get_campaign_q_codes(campaign_code: CampaignCode) -> list[QuestionCode]:
    """Get campaign question codes"""

    # All campaigns have q1
    q_codes = [QuestionCode.q1]

    # Campaigns with q2
    if (
        campaign_code == CampaignCode.economic_empowerment_mexico
        or campaign_code == CampaignCode.healthwellbeing
    ):
        q_codes.append(QuestionCode.q2)

    return q_codes


def check_campaign(campaign: str) -> CampaignCode:
    """Check if campaign exists"""

    if campaign.lower() in [c.lower() for c in constants.CAMPAIGN_CODES]:
        for campaign_code in CampaignCode:
            if campaign_code.value == campaign:
                return campaign_code


def check_language(lang: str = "en") -> str:
    """Check if language exists, if not, default to 'en'"""

    if lang in constants.TRANSLATION_LANGUAGES:
        return lang
    else:
        return "en"


def check_q_code_for_campaign(q_code: str, campaign_code: CampaignCode) -> QuestionCode:
    """Check if q code str exists for campaign and return the q code"""

    for q in get_campaign_q_codes(campaign_code=campaign_code):
        if q.value == q_code:
            return q


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
        os.remove(filename)


def get_q_code_column_names() -> list:
    """Get q code column names"""

    columns = []
    for q_code in QuestionCode:
        columns.extend(
            [
                f"{q_code.value}_raw_response",
                f"{q_code.value}_original_language",
                f"{q_code.value}_canonical_code",
                f"{q_code.value}_lemmatized",
                f"{q_code.value}_tokenized",
                f"{q_code.value}_parent_category",
            ]
        )

    return columns


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
    data_lists: list[list[dict]], by_key: str, keys_to_merge: list[str]
) -> list[dict]:
    """
    Given a list containing a list of dictionaries, find duplicates by a specific dictionary key and merge them to a
    single list.

    :param data_lists: A list containing lists of dictionaries.
    :param by_key: Key to use for checking duplicates.
    :param keys_to_merge: If the value of the key is an int, add the value to an existing dictionary with same key.
    """

    # Flatten the list
    data_lists_flattened: list[dict] = []
    for data_lists in data_lists:
        data_lists_flattened.extend([x for x in data_lists if x])

    tmp_merged: dict[str, dict] = {}
    for data in data_lists_flattened:
        data_key_value = data.get(by_key)
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
