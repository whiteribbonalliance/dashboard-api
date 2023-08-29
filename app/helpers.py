import glob
import os
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


async def check_campaign(campaign: str) -> CampaignCode:
    """Check if campaign exists"""

    if campaign.lower() in [c.lower() for c in constants.CAMPAIGN_CODES]:
        for campaign_code in CampaignCode:
            if campaign_code.value == campaign:
                return campaign_code


async def check_language(lang: str) -> str:
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


def clear_tmp_dir():
    """Clear tmp dir"""

    if not os.path.isdir("/tmp"):
        return

    for filename in glob.glob("/tmp/wra_*"):
        os.remove(filename)
