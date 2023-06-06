import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api import dependencies
from app.enums.campaign_code import CampaignCode
from app.logginglib import init_custom_logger
from app.schemas.campaign import Campaign
from app.schemas.campaign_request import CampaignRequest
from app.schemas.filter_options import FilterOptions
from app.services.campaign import CampaignCRUD, CampaignService

logger = logging.getLogger(__name__)
init_custom_logger(logger)

router = APIRouter(prefix="/campaigns")


# TODO: Cache responses for as long as data has not been reloaded from BigQuery


@router.post(
    path="/{campaign}",
    response_model=Campaign,
    status_code=status.HTTP_200_OK,
)
async def read_campaign(
    commons: Annotated[dict, Depends(dependencies.common_parameters)],
    campaign_req: CampaignRequest,
):
    """Read a campaign"""

    campaign_code = commons.get("campaign_code")

    campaign_service = CampaignService(
        campaign_code=campaign_code,
        filter_1=campaign_req.filter_1,
        filter_2=campaign_req.filter_2,
    )

    campaign_crud = CampaignCRUD(campaign_code=campaign_code)

    # Top words and phrases
    top_words_and_phrases = {
        "top_words": campaign_service.get_top_words(),
        "two_word_phrases": campaign_service.get_two_word_phrases(),
        "three_word_phrases": campaign_service.get_three_word_phrases(),
        "wordcloud_words": campaign_service.get_wordcloud_words(),
    }

    # Responses sample
    responses_sample = {
        "columns": campaign_crud.get_responses_sample_columns(),
        "data": campaign_service.get_responses_sample_data(),
    }

    # Responses breakdown
    responses_breakdown = campaign_service.get_responses_breakdown_data()

    # Description
    filter_1_description = campaign_service.get_filter_1_description()
    filter_2_description = campaign_service.get_filter_2_description()

    # Respondents count
    filter_1_respondents_count = campaign_service.get_filter_1_respondents_count()
    filter_2_respondents_count = campaign_service.get_filter_2_respondents_count()

    # Average age
    filter_1_average_age = campaign_service.get_filter_1_average_age()
    filter_2_average_age = campaign_service.get_filter_2_average_age()

    # Histogram
    histogram = campaign_service.get_histogram()

    return Campaign(
        responses_sample=responses_sample,
        responses_breakdown=responses_breakdown,
        top_words_and_phrases=top_words_and_phrases,
        histogram=histogram,
        filter_1_description=filter_1_description,
        filter_2_description=filter_2_description,
        filter_1_respondents_count=filter_1_respondents_count,
        filter_2_respondents_count=filter_2_respondents_count,
        filter_1_average_age=filter_1_average_age,
        filter_2_average_age=filter_2_average_age,
    )


@router.get(
    path="/{campaign}/filter-options",
    response_model=FilterOptions,
    status_code=status.HTTP_200_OK,
)
async def read_filter_options(
    commons: Annotated[dict, Depends(dependencies.common_parameters)]
):
    """Read a campaign's filter options"""

    campaign_code: CampaignCode = commons.get("campaign_code")

    campaign_service = CampaignService(campaign_code=campaign_code)
    campaign_crud = CampaignCRUD(campaign_code=campaign_code)

    # Country options
    countries = campaign_crud.get_countries_list()
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
    response_topics = campaign_service.get_response_topics()
    response_topic_options = [
        {"value": response_topic.code, "label": response_topic.name}
        for response_topic in response_topics
    ]

    # Ages options
    ages = campaign_crud.get_ages()
    ages = [{"value": age, "label": age} for age in ages]

    # Gender options
    genders = campaign_crud.get_genders()
    gender_options = [{"value": gender, "label": gender} for gender in genders]

    # Profession options
    professions = campaign_crud.get_professions()
    profession_options = [
        {"value": profession, "label": profession} for profession in professions
    ]

    # Only responses from categories options
    only_responses_from_categories_options = (
        campaign_crud.get_only_responses_from_categories_options()
    )

    # Only multi-word phrases containing filter term options
    only_multi_word_phrases_containing_filter_term_options = (
        campaign_crud.get_only_multi_word_phrases_containing_filter_term_options()
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
