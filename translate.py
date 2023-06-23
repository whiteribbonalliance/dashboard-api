"""
Apply translations
"""

import asyncio

from app import constants
from app.api.v1.endpoints.campaigns import (
    read_campaign,
    read_filter_options,
    read_who_the_people_are_options,
)
from app.core.settings import settings
from app.schemas.campaign_request import CampaignRequest
from app.schemas.common_parameters import CommonParameters
from app.services.translator import Translator
from app.utils import data_loader

settings.OFFLINE_TRANSLATE_MODE = True
data_loader.load_data()
count_chars_only = False
translator = Translator()


async def translate():
    """
    Apply translation for each language in a campaign

    Will skip 'app.services.campaign.get_responses_sample()' as this contains random data (is translated on the fly)
    """

    # Translate each campaign
    for campaign_code in constants.CAMPAIGN_CODES:
        for language in constants.TRANSLATION_LANGUAGES:
            if count_chars_only:
                print(f"Counting characters for {campaign_code}-{language}...")
            else:
                print(f"Translating texts for {campaign_code}-{language}...")

            common_parameters = CommonParameters(
                campaign_code=campaign_code, language=language
            )
            campaign_req = CampaignRequest()

            # Extract texts from each endpoint
            # With OFFLINE_TRANSLATE_MODE = True, texts will be extracted into Translator when calling
            # the functions below
            await read_campaign(
                common_parameters=common_parameters, campaign_req=campaign_req
            )
            await read_filter_options(common_parameters=common_parameters)
            await read_who_the_people_are_options(common_parameters=common_parameters)

            # Translate extracted texts
            translator.translate_extracted_texts(count_chars_only=count_chars_only)

    # Print
    if count_chars_only:
        print(
            f"\nTotal Characters count from texts that can be translated: {translator.get_translations_char_count()}"
        )
    else:
        print(
            f"\nTotal Characters count from texts translated: {translator.get_translations_char_count()}"
        )


asyncio.run(translate())
