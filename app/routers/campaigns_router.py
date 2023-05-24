import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.constants import CAMPAIGNS_LIST
from app.enums.api_prefix import ApiPrefix
from app.enums.campaign_code import CampaignCode
from app.http_exceptions import ResourceNotFoundHTTPException
from app.logginglib import init_custom_logger
from app.schemas.campaign import Campaign
from app.schemas.campaign_request import CampaignRequest
from app.schemas.country import Country
from app.schemas.filter_options import FilterOptions
from app.utils.data_reader import DataReader

logger = logging.getLogger(__name__)
init_custom_logger(logger)

router = APIRouter(prefix=f"/{ApiPrefix.v1}/campaigns")


async def common_parameters(campaign: str) -> dict[str, CampaignCode]:
    """Verify a campaign and return the common parameter"""

    campaign_code_verified = verify_campaign(campaign=campaign)

    return {"campaign_code": campaign_code_verified}


@router.post(
    path="/{campaign}",
    response_model=Campaign,
    status_code=status.HTTP_200_OK,
)
async def read_campaign(
    commons: Annotated[dict, Depends(common_parameters)],
    campaign_req: CampaignRequest,
):
    """Read campaign"""

    campaign_code = commons.get("campaign_code")

    return Campaign(data="123")


@router.get(
    path="/{campaign}/filter-options",
    response_model=FilterOptions,
    status_code=status.HTTP_200_OK,
)
async def read_filter_options(commons: Annotated[dict, Depends(common_parameters)]):
    """Read filter options"""

    campaign_code: CampaignCode = commons.get("campaign_code")

    data_reader = DataReader(campaign_code=campaign_code)

    # Country options
    countries = data_reader.get_countries_list()
    country_options = [
        {"value": country.alpha2_code, "label": country.name} for country in countries
    ]

    # Response topic options
    response_topics = data_reader.get_response_topics()
    response_topic_options = [
        {"value": response_topic.code, "label": response_topic.name}
        for response_topic in response_topics
    ]

    # Age bucket options
    age_buckets = data_reader.get_age_buckets()
    age_bucket_options = [
        {"value": age_bucket, "label": age_bucket} for age_bucket in age_buckets
    ]

    # Gender options
    genders = data_reader.get_genders()
    gender_options = [{"value": gender, "label": gender} for gender in genders]

    # Profession options
    professions = data_reader.get_professions()
    profession_options = [
        {"value": profession, "label": profession} for profession in professions
    ]

    # Only responses from categories options
    only_responses_from_categories_options = (
        data_reader.get_only_responses_from_categories_options()
    )

    # Only multi-word phrases containing filter term options
    only_multi_word_phrases_containing_filter_term_options = (
        data_reader.get_only_multi_word_phrases_containing_filter_term_options()
    )

    return FilterOptions(
        countries=country_options,
        response_topics=response_topic_options,
        age_buckets=age_bucket_options,
        genders=gender_options,
        professions=profession_options,
        only_responses_from_categories=only_responses_from_categories_options,
        only_multi_word_phrases_containing_filter_term=only_multi_word_phrases_containing_filter_term_options,
    )


@router.get(
    path="/{campaign}/countries/{country_alpha2_code}",
    response_model=Country,
    status_code=status.HTTP_200_OK,
)
async def read_country(
    commons: Annotated[dict, Depends(common_parameters)],
    country_alpha2_code: str,
):
    """Read country"""

    campaign_code: CampaignCode = commons.get("campaign_code")
    verify_country(campaign_code=campaign_code, country_alpha2_code=country_alpha2_code)

    data_reader = DataReader(campaign_code=campaign_code)

    countries = data_reader.get_countries_dict()
    country = countries.get(country_alpha2_code)

    return country


def verify_campaign(campaign: str) -> CampaignCode:
    """
    Check if campaign exists, If not, raise an exception

    :param campaign: The campaign
    """

    if campaign.lower() not in [c.lower() for c in CAMPAIGNS_LIST]:
        raise ResourceNotFoundHTTPException("Campaign not found")

    if campaign == CampaignCode.what_women_want:
        return CampaignCode.what_women_want
    if campaign == CampaignCode.what_young_people_want:
        return CampaignCode.what_young_people_want
    if campaign == CampaignCode.midwives_voices:
        return CampaignCode.midwives_voices


def verify_country(campaign_code: CampaignCode, country_alpha2_code: str):
    """
    Check if country exists in campaign, If not, raise an exception

    :param campaign_code: The campaign
    :param country_alpha2_code: The country's alpha2 code
    """

    data_reader = DataReader(campaign_code=campaign_code)

    countries = data_reader.get_countries_dict()
    country = countries.get(country_alpha2_code)
    if not country:
        raise ResourceNotFoundHTTPException("Country not found")

    return True
