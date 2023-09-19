import glob
import os
import random
import re
from typing import Literal

import numpy as np

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


def get_unique_flattened_list(
    data_lists: list[list[dict]], content_type: Literal["dict", "str"]
) -> list[dict | str]:
    """Get unique flattened list that contains dict or str"""

    # Flatten list
    data_lists_flatten: list[dict | str] = []
    for data_list in data_lists:
        data_lists_flatten.extend([dict(x) for x in data_list if x])

    if content_type == "dict":
        return [
            dict(tupleized)
            for tupleized in set(
                tuple(data_list.items()) for data_list in data_lists_flatten
            )
        ]
    elif content_type == "list":
        return list(set(data_lists_flatten))
    else:
        return []


def get_distributed_data_list(data_lists: list[list]) -> list:
    """Get distribute data list"""

    distributed_data_list = []

    # Get items count of list with most items
    max_items_count = max([len(data_list) for data_list in data_lists])

    # Get average items count
    average_items_count = max_items_count // len(data_lists)

    # Get sample from each list
    for data_list in data_lists:
        if data_list:
            n_sample = average_items_count
            if average_items_count > len(data_list):
                n_sample = len(data_list)
            distributed_data_list.extend(
                random.sample(population=data_list, k=n_sample)
            )

    return distributed_data_list
