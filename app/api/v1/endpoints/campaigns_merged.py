"""
MIT License

Copyright (c) 2023 White Ribbon Alliance. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import logging

from fastapi import APIRouter, Depends, Request, status

from app import crud
from app.api import dependencies
from app.helpers.campaigns_config_loader import CAMPAIGNS_CONFIG
from app.logginglib import init_custom_logger
from app.schemas.campaign import Campaign
from app.schemas.campaign_request import CampaignRequest
from app.schemas.filter_options import FilterOptions
from app.schemas.option_str import OptionStr
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
    campaign_req: CampaignRequest,
    _request: Request,
    language: str = Depends(dependencies.language_check),
):
    """Read campaigns merged"""

    filter_1 = campaign_req.filter_1
    filter_2 = campaign_req.filter_2

    # Get all campaigns data
    campaigns: dict[str, list[Campaign]] = {}
    for campaign_config in CAMPAIGNS_CONFIG.values():
        # CRUD
        campaign_crud = crud.Campaign(campaign_code=campaign_config.campaign_code)

        # Campaign q codes
        campaign_q_codes = campaign_crud.get_q_codes()

        # Campaign data
        for campaign_q_code in campaign_q_codes:
            # Campaign service
            campaign_service = CampaignService(
                campaign_code=campaign_config.campaign_code,
                language=language,
                filter_1=filter_1,
                filter_2=filter_2,
            )

            if not campaigns.get(campaign_config.campaign_code):
                campaigns[campaign_config.campaign_code] = []
            campaigns[campaign_config.campaign_code].append(
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
    _request: Request, language: str = Depends(dependencies.language_check)
):
    """Read filter options for campaigns merged"""

    # Get all campaigns filter options
    campaigns_filter_options: list[dict] = []
    for campaign_config in CAMPAIGNS_CONFIG.values():
        # Campaign service
        campaign_service = CampaignService(
            campaign_code=campaign_config.campaign_code, language=language
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
    response_model=list[OptionStr],
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
def histogram_options(
    _request: Request, language: str = Depends(dependencies.language_check)
):
    """Read histogram options for campaign"""

    # Get all campaigns histogram options
    campaigns_histogram_options: list[list[dict]] = []
    for campaign_config in CAMPAIGNS_CONFIG.values():
        # Campaign service
        campaign_service = CampaignService(
            campaign_code=campaign_config.campaign_code, language=language
        )

        # Histogram options
        campaign_histogram_options = campaign_service.get_histogram_options()
        campaigns_histogram_options.append([x for x in campaign_histogram_options])

    # Service
    campaigns_merged_service = CampaignsMergedService(
        language=language,
        campaigns_histogram_options=campaigns_histogram_options,
    )

    # Histogram options
    options = campaigns_merged_service.get_histogram_options()

    return options
