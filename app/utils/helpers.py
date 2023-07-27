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


def campaign_has_q2(campaign_code: CampaignCode) -> bool:
    """Check if campaign has q2"""

    if campaign_code in constants.CAMPAIGNS_WITH_Q2:
        return True

    return False
