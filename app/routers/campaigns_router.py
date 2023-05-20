import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.constants import CAMPAIGNS_LIST
from app.enums.api_prefix import ApiPrefix
from app.exceptions import ResourceNotFoundHTTPException
from app.logginglib import init_custom_logger
from app.schemas.campaign import CampaignRequest, CampaignResponse
from app.schemas.country import CountryResponse
from app.schemas.filter_options import FilterOptionsResponse
from app.utils import code_hierarchy
from app.utils import countries_filter

logger = logging.getLogger(__name__)
init_custom_logger(logger)

router = APIRouter(prefix=f"/{ApiPrefix.v1}/campaigns")


async def common_parameters(campaign: str):
    verify_campaign(campaign=campaign)

    return {"campaign": campaign}


@router.post(
    path="/{campaign}",
    response_model=CampaignResponse,
    status_code=status.HTTP_200_OK,
)
async def read_campaign(
    commons: Annotated[dict, Depends(common_parameters)],
    campaign_req: CampaignRequest,
):
    """Get campaign"""

    campaign = commons.get("campaign")

    return CampaignResponse(data="123")


@router.get(
    path="/{campaign}/filter-options",
    response_model=FilterOptionsResponse,
    status_code=status.HTTP_200_OK,
)
async def read_filter_options(commons: Annotated[dict, Depends(common_parameters)]):
    """Get filter options"""

    campaign = commons.get("campaign")

    countries = countries_filter.get_unique_countries(campaign=campaign)
    response_topics = code_hierarchy.get_response_topics(campaign=campaign)

    return FilterOptionsResponse(countries=countries, response_topics=response_topics)


@router.get(
    path="/{campaign}/countries/{country_alpha2_code}",
    response_model=CountryResponse,
    status_code=status.HTTP_200_OK,
)
async def read_country_regions(
    commons: Annotated[dict, Depends(common_parameters)],
    country_alpha2_code: str,
):
    """Get country"""

    campaign = commons.get("campaign")

    verify_country(campaign=campaign, country_alpha2_code=country_alpha2_code)

    regions = countries_filter.get_country_regions(
        campaign=campaign, country_alpha2_code=country_alpha2_code
    )

    return CountryResponse(regions=regions)


def verify_campaign(campaign: str):
    """
    Check if campaign exists, If not, raise an exception

    :param campaign: The campaign
    """

    if campaign.lower() not in [c.lower() for c in CAMPAIGNS_LIST]:
        raise ResourceNotFoundHTTPException("Campaign not found")

    return True


def verify_country(campaign: str, country_alpha2_code: str):
    """
    Check if country exists in campaign, If not, raise an exception

    :param campaign: The campaign
    :param country_alpha2_code: The country's alpha2 code
    """

    countries = countries_filter.get_unique_countries(campaign=campaign)
    if country_alpha2_code.lower() not in [c.get("value").lower() for c in countries]:
        raise ResourceNotFoundHTTPException("Country not found")

    return True
