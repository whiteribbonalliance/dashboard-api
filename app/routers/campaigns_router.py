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
from app.schemas.filter_options import FilterOptions
from app.utils.data_access_layer import DataAccessLayer

logger = logging.getLogger(__name__)
init_custom_logger(logger)

router = APIRouter(prefix=f"/{ApiPrefix.v1}/campaigns")


# TODO: Cache responses for as long as data has not been reloaded from BigQuery


async def common_parameters(campaign: str) -> dict[str, CampaignCode]:
    """Verify the campaign and return the common parameter"""

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

    dal = DataAccessLayer(
        campaign_code=campaign_code,
        filter_1=campaign_req.filter_1,
        filter_2=campaign_req.filter_2,
    )

    # Only filter 1 will be applied
    responses_sample = {
        "columns": dal.get_responses_sample_columns(),
        "data": dal.get_responses_sample_data(),
    }

    # Only filter 1 will be applied
    responses_breakdown = dal.get_responses_breakdown_data()

    return Campaign(
        responses_sample=responses_sample, responses_breakdown=responses_breakdown
    )


@router.get(
    path="/{campaign}/filter-options",
    response_model=FilterOptions,
    status_code=status.HTTP_200_OK,
)
async def read_filter_options(commons: Annotated[dict, Depends(common_parameters)]):
    """Read filter options"""

    campaign_code: CampaignCode = commons.get("campaign_code")

    dal = DataAccessLayer(campaign_code=campaign_code)

    # Country options
    countries = dal.get_countries_list()
    country_options = [
        {"value": country.alpha2_code, "label": country.name} for country in countries
    ]

    # Country regions options
    country_regions_options = []
    for country in countries:
        regions_options = {"country_alpha2_code": country.alpha2_code, "options": []}
        for region in country.regions:
            regions_options["options"].append({"value": region, "label": region})
        country_regions_options.append(regions_options)

    # Response topic options
    response_topics = dal.get_response_topics()
    response_topic_options = [
        {"value": response_topic.code, "label": response_topic.name}
        for response_topic in response_topics
    ]

    # Ages options
    ages = dal.get_ages()
    ages = [{"value": age, "label": age} for age in ages]

    # Gender options
    genders = dal.get_genders()
    gender_options = [{"value": gender, "label": gender} for gender in genders]

    # Profession options
    professions = dal.get_professions()
    profession_options = [
        {"value": profession, "label": profession} for profession in professions
    ]

    # Only responses from categories options
    only_responses_from_categories_options = (
        dal.get_only_responses_from_categories_options()
    )

    # Only multi-word phrases containing filter term options
    only_multi_word_phrases_containing_filter_term_options = (
        dal.get_only_multi_word_phrases_containing_filter_term_options()
    )

    return FilterOptions(
        countries=country_options,
        country_regions=country_regions_options,
        response_topics=response_topic_options,
        ages=ages,
        genders=gender_options,
        professions=profession_options,
        only_responses_from_categories=only_responses_from_categories_options,
        only_multi_word_phrases_containing_filter_term=only_multi_word_phrases_containing_filter_term_options,
    )


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
