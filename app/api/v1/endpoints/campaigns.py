import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app import auth_handler
from app.api import dependencies
from app import databases
from app.enums.campaign_code import CampaignCode
from app.logginglib import init_custom_logger
from app.schemas.campaign import Campaign
from app.schemas.campaign_request import CampaignRequest
from app.schemas.common_parameters_campaigns import CommonParametersCampaigns
from app.schemas.filter_options import FilterOptions
from app.services.api_cache import ApiCache
from app.services.campaign import CampaignService

logger = logging.getLogger(__name__)
init_custom_logger(logger)

router = APIRouter(prefix="/campaigns")

api_cache = ApiCache()


@router.post(
    path="/{campaign}",
    response_model=Campaign,
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
async def read_campaign(
    common_parameters: Annotated[
        CommonParametersCampaigns, Depends(dependencies.common_parameters_campaigns)
    ],
    campaign_req: CampaignRequest,
):
    """Read a campaign"""

    campaign_code = common_parameters.campaign_code
    language = common_parameters.language
    q_code = common_parameters.q_code

    filter_1 = campaign_req.filter_1
    filter_2 = campaign_req.filter_2

    # Create service
    campaign_service = CampaignService(
        campaign_code=campaign_code,
        language=language,
        filter_1=filter_1,
        filter_2=filter_2,
    )

    # Top words and phrases
    top_words_and_phrases = {
        "top_words": campaign_service.get_top_words(q_code=q_code),
        "two_word_phrases": campaign_service.get_two_word_phrases(q_code=q_code),
        "three_word_phrases": campaign_service.get_three_word_phrases(q_code=q_code),
        "wordcloud_words": campaign_service.get_wordcloud_words(q_code=q_code),
    }

    # Responses sample
    responses_sample = {
        "columns": campaign_service.get_responses_sample_columns(q_code=q_code),
        "data": campaign_service.get_responses_sample(q_code=q_code),
    }

    # Responses breakdown
    responses_breakdown = campaign_service.get_responses_breakdown(q_code=q_code)

    # Living settings breakdown
    living_settings_breakdown = campaign_service.get_living_settings_breakdown()

    # Histogram
    histogram = campaign_service.get_histogram()

    # Genders breakdown
    if campaign_code == CampaignCode.what_young_people_want:
        genders_breakdown = campaign_service.get_genders_breakdown()
    else:
        genders_breakdown = []

    # World bubble maps coordinates
    world_bubble_maps_coordinates = campaign_service.get_world_bubble_maps_coordinates()

    # Respondents count
    filter_1_respondents_count = campaign_service.get_filter_1_respondents_count()
    filter_2_respondents_count = campaign_service.get_filter_2_respondents_count()

    # Average age
    filter_1_average_age = campaign_service.get_filter_1_average_age()
    filter_2_average_age = campaign_service.get_filter_2_average_age()

    # Filters Description
    filter_1_description = campaign_service.get_filter_1_description()
    filter_2_description = campaign_service.get_filter_2_description()

    # Filters are identical
    filters_are_identical = campaign_service.get_filters_are_identical()

    return Campaign(
        responses_sample=responses_sample,
        responses_breakdown=responses_breakdown,
        living_settings_breakdown=living_settings_breakdown,
        top_words_and_phrases=top_words_and_phrases,
        histogram=histogram,
        genders_breakdown=genders_breakdown,
        world_bubble_maps_coordinates=world_bubble_maps_coordinates,
        filter_1_respondents_count=filter_1_respondents_count,
        filter_2_respondents_count=filter_2_respondents_count,
        filter_1_average_age=filter_1_average_age,
        filter_2_average_age=filter_2_average_age,
        filter_1_description=filter_1_description,
        filter_2_description=filter_2_description,
        filters_are_identical=filters_are_identical,
    )


@router.get(
    path="/{campaign}/filter-options",
    response_model=FilterOptions,
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
async def read_filter_options(
    common_parameters: Annotated[
        CommonParametersCampaigns, Depends(dependencies.common_parameters_campaigns)
    ]
):
    """Read filter options for campaign"""

    campaign_code = common_parameters.campaign_code
    language = common_parameters.language

    # Create service
    campaign_service = CampaignService(campaign_code=campaign_code, language=language)

    # Country options
    countries = campaign_service.get_countries_list()
    country_options = [
        {"value": country.alpha2_code, "label": country.name} for country in countries
    ]

    # Country regions options
    country_regions_options = []
    for country in countries:
        regions_options = {"country_alpha2_code": country.alpha2_code, "options": []}
        for region in sorted(country.regions, key=lambda r: r.name):
            regions_options["options"].append(
                {"value": region.code, "label": region.name}
            )
        country_regions_options.append(regions_options)

    # Response topic options
    response_topics = campaign_service.get_response_topics()
    response_topic_options = [
        {
            "value": response_topic.code,
            "label": response_topic.name,
            "metadata": "is_parent" if response_topic.is_parent else "is_not_parent",
        }
        for response_topic in response_topics
    ]

    # Age options
    ages = campaign_service.get_ages()
    ages = [{"value": age.code, "label": age.name} for age in ages]

    # Gender options
    genders = campaign_service.get_genders()
    gender_options = [
        {"value": gender.code, "label": gender.name} for gender in genders
    ]

    # Profession options
    professions = campaign_service.get_professions()
    profession_options = [
        {"value": profession.code, "label": profession.name}
        for profession in professions
    ]

    # Only responses from categories options
    only_responses_from_categories_options = (
        campaign_service.get_only_responses_from_categories_options()
    )

    # Only multi-word phrases containing filter term options
    only_multi_word_phrases_containing_filter_term_options = (
        campaign_service.get_only_multi_word_phrases_containing_filter_term_options()
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


@router.get(
    path="/{campaign}/who-the-people-are-options",
    response_model=list,
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
async def read_who_the_people_are_options(
    common_parameters: Annotated[
        CommonParametersCampaigns, Depends(dependencies.common_parameters_campaigns)
    ]
):
    """Read who the people are options for campaign"""

    campaign_code = common_parameters.campaign_code
    language = common_parameters.language

    # Create service
    campaign_service = CampaignService(campaign_code=campaign_code, language=language)

    # Options
    options = campaign_service.get_who_the_people_are_options()

    return options


@router.get("/{campaign}/data", status_code=status.HTTP_200_OK)
async def read_user(
    username: str = Depends(auth_handler.auth_wrapper_access_token),
):
    """Read campaign data"""

    return {"test": username}
