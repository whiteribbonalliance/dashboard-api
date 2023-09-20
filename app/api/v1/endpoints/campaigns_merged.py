import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api import dependencies
from app.api.v1.endpoints import campaigns as campaigns_endpoints
from app.enums.campaign_code import CampaignCode
from app.logginglib import init_custom_logger
from app.schemas.campaign import Campaign
from app.schemas.campaign_request import CampaignRequest
from app.schemas.common_parameters_all_campaigns import CommonParametersAllCampaigns
from app.schemas.common_parameters_campaign import CommonParametersCampaign
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
        CommonParametersAllCampaigns,
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
    campaigns_merged_service = CampaignsMergedService(campaigns=campaigns)

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
