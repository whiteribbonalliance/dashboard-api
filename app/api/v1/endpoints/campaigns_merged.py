import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api import dependencies
from app.api.v1.endpoints import campaigns as campaigns_endpoints
from app.enums.campaign_code import CampaignCode
from app.logginglib import init_custom_logger
from app.schemas.campaign import Campaign
from app.schemas.campaign_request import CampaignRequest
from app.schemas.common_parameters_campaign import CommonParametersCampaign
from app.schemas.common_parameters_campaigns_merged import (
    CommonParametersCampaignsMerged,
)
from app.schemas.filter_options import FilterOptions
from app.services.api_cache import ApiCache
from app.services.campaigns_merged import CampaignsMergedService

logger = logging.getLogger(__name__)
init_custom_logger(logger)

router = APIRouter(prefix="/campaigns-merged")

api_cache = ApiCache()


@router.post(
    path="",
    response_model=Campaign,
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
async def read_campaigns_merged(
    parameters: Annotated[
        CommonParametersCampaignsMerged,
        Depends(dependencies.dep_common_parameters_all_campaigns),
    ],
    campaign_req: CampaignRequest,
):
    """Read campaigns merged"""

    language = parameters.language
    request = parameters.request
    q_code = parameters.q_code

    # Get all campaigns
    campaigns: list[Campaign] = []
    for campaign_code in CampaignCode:
        # TODO: Temporarily skip campaign 'wee'
        if campaign_code == CampaignCode.womens_economic_empowerment:
            continue

        parameters = CommonParametersCampaign(
            campaign_code=campaign_code,
            language=language,
            request=request,
            q_code=q_code,
        )

        campaign = await campaigns_endpoints.read_campaign(
            parameters=parameters, campaign_req=campaign_req
        )

        campaigns.append(campaign)

    # Service
    campaigns_merged_service = CampaignsMergedService(
        campaigns=campaigns, campaigns_filter_options=[]
    )

    # Responses sample
    responses_sample = campaigns_merged_service.get_responses_sample()

    # Responses breakdown
    responses_breakdown = campaigns_merged_service.get_responses_breakdown()

    # Living settings breakdown
    # living_settings_breakdown = campaigns_merged_service.get_living_settings_breakdown()

    # Top words or phrases
    top_words_and_phrases = campaigns_merged_service.get_top_words_and_phrases()

    # Histogram
    histogram = campaigns_merged_service.get_histogram()

    # Genders breakdown
    # genders_breakdown = campaigns_merged_service.get_genders_breakdown()

    # World bubble maps coordinates
    world_bubble_maps_coordinates = (
        campaigns_merged_service.get_world_bubble_maps_coordinates()
    )

    # Filter 1 respondents count
    filter_1_respondents_count = (
        campaigns_merged_service.get_filter_1_respondents_count()
    )

    # Filter 2 respondents count
    filter_2_respondents_count = (
        campaigns_merged_service.get_filter_2_respondents_count()
    )

    # Filter 1 average age
    filter_1_average_age = campaigns_merged_service.get_filter_1_average_age()

    # Filter 2 average age
    filter_2_average_age = campaigns_merged_service.get_filter_2_average_age()

    # Filter 1 description
    filter_1_description = campaigns_merged_service.get_filter_1_description()

    # Filter 2 description
    filter_2_description = campaigns_merged_service.get_filter_2_description()

    # Filters are identical
    filters_are_identical = campaigns_merged_service.get_filters_are_identical()

    return Campaign(
        campaign_code="",
        responses_sample=responses_sample,
        responses_breakdown=responses_breakdown,
        living_settings_breakdown=[],
        top_words_and_phrases=top_words_and_phrases,
        histogram=histogram,
        genders_breakdown=[],
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
    path="/filter-options",
    response_model=FilterOptions,
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
async def read_filter_options(
    parameters: Annotated[
        CommonParametersCampaignsMerged,
        Depends(dependencies.dep_common_parameters_all_campaigns),
    ]
):
    """Read filter options for campaigns merged"""

    language = parameters.language
    request = parameters.request
    q_code = parameters.q_code

    campaigns_filter_options: list[FilterOptions] = []

    # Get campaigns filter options
    for campaign_code in CampaignCode:
        parameters = CommonParametersCampaign(
            campaign_code=campaign_code,
            language=language,
            request=request,
            q_code=q_code,
        )
        campaigns_filter_options.append(
            await campaigns_endpoints.read_filter_options(parameters=parameters)
        )

    # Service
    campaigns_merged_service = CampaignsMergedService(
        campaigns=[], campaigns_filter_options=campaigns_filter_options
    )

    # Country options
    country_options = campaigns_merged_service.get_country_options()

    # Country regions options
    country_regions_options = campaigns_merged_service.get_country_regions_options()

    # Response topic options
    response_topics_options = campaigns_merged_service.get_response_topics_options()

    # Only responses from categories options
    only_responses_from_categories_options = (
        campaigns_merged_service.get_only_responses_from_categories_options()
    )

    # Only multi-word phrases containing filter term
    only_multi_word_phrases_containing_filter_term_options = (
        campaigns_merged_service.get_only_multi_word_phrases_containing_filter_term_options()
    )

    return FilterOptions(
        countries=country_options,
        country_regions=country_regions_options,
        response_topics=response_topics_options,
        ages=[],
        genders=[],
        professions=[],
        only_responses_from_categories=only_responses_from_categories_options,
        only_multi_word_phrases_containing_filter_term=only_multi_word_phrases_containing_filter_term_options,
    )
