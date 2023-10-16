import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api import dependencies
from app.crud.campaign import CampaignCRUD
from app.enums.campaign_code import CampaignCode
from app.logginglib import init_custom_logger
from app.schemas.campaign import Campaign
from app.schemas.campaign_request import CampaignRequest
from app.schemas.common_parameters_campaigns_merged import (
    CommonParametersCampaignsMerged,
)
from app.schemas.filter_options import FilterOptions
from app.schemas.option import Option
from app.services.api_cache import ApiCache
from app.services.campaign import CampaignService
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
def read_campaigns_merged(
    parameters: Annotated[
        CommonParametersCampaignsMerged,
        Depends(dependencies.dep_common_parameters_all_campaigns),
    ],
    campaign_req: CampaignRequest,
):
    """Read campaigns merged"""

    language = parameters.language
    filter_1 = campaign_req.filter_1
    filter_2 = campaign_req.filter_2

    # Get all campaigns data
    campaigns: dict[str, list[Campaign]] = {}
    for campaign_code in CampaignCode:
        # TODO: Temporarily skip campaign 'wee'
        if campaign_code == CampaignCode.womens_economic_empowerment:
            continue

        # CRUD
        crud = CampaignCRUD(campaign_code=campaign_code)

        # Campaign q codes
        campaign_q_codes = crud.get_q_codes()

        # Campaign data
        for campaign_q_code in campaign_q_codes:
            # Campaign service
            campaign_service = CampaignService(
                campaign_code=campaign_code,
                language=language,
                filter_1=filter_1,
                filter_2=filter_2,
            )

            if not campaigns.get(campaign_code.value):
                campaigns[campaign_code.value] = []
            campaigns[campaign_code.value].append(
                campaign_service.get_campaign(
                    q_code=campaign_q_code,
                    include_list_of_ages=False,
                    include_list_of_age_buckets_default=True,
                )
            )

    # Service
    campaigns_merged_service = CampaignsMergedService(
        language=language,
        campaigns_data=campaigns,
        filter_1=filter_1,
        filter_2=filter_2,
    )

    # Campaign
    campaign = campaigns_merged_service.get_campaign()

    return campaign


@router.get(
    path="/filter-options",
    response_model=FilterOptions,
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
def read_filter_options(
    parameters: Annotated[
        CommonParametersCampaignsMerged,
        Depends(dependencies.dep_common_parameters_all_campaigns),
    ]
):
    """Read filter options for campaigns merged"""

    language = parameters.language

    # Get all campaigns filter options
    campaigns_filter_options: list[dict] = []
    for campaign_code in CampaignCode:
        # TODO: Temporarily skip campaign 'wee'
        if campaign_code == CampaignCode.womens_economic_empowerment:
            continue

        # Campaign service
        campaign_service = CampaignService(
            campaign_code=campaign_code, language=language
        )

        # Filter options
        campaign_filter_options = campaign_service.get_filter_options()
        campaigns_filter_options.append(campaign_filter_options.dict())

    # Service
    campaigns_merged_service = CampaignsMergedService(
        language=language, campaigns_filter_options=campaigns_filter_options
    )

    # Filter options
    filter_options = campaigns_merged_service.get_filter_options()

    return filter_options


@router.get(
    path="/histogram-options",
    response_model=list[Option],
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
def histogram_options(
    parameters: Annotated[
        CommonParametersCampaignsMerged,
        Depends(dependencies.dep_common_parameters_all_campaigns),
    ]
):
    """Read histogram options for campaign"""

    language = parameters.language

    # Get all campaigns histogram options
    campaigns_histogram_options: list[list[dict]] = []
    for campaign_code in CampaignCode:
        # TODO: Temporarily skip campaign 'wee'
        if campaign_code == CampaignCode.womens_economic_empowerment:
            continue

        # Campaign service
        campaign_service = CampaignService(
            campaign_code=campaign_code, language=language
        )

        # Histogram options
        campaign_histogram_options = campaign_service.histogram_options()
        campaigns_histogram_options.append(
            [x.dict() for x in campaign_histogram_options]
        )

    # Service
    campaigns_merged_service = CampaignsMergedService(
        language=language,
        campaigns_histogram_options=campaigns_histogram_options,
    )

    # Histogram options
    options = campaigns_merged_service.get_histogram_options()

    return options
