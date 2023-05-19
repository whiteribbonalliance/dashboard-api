import logging

from fastapi import APIRouter, status

from app.constants import CAMPAIGNS_LIST
from app.enums.api_prefix import ApiPrefix
from app.exceptions import ResourceNotFoundHTTPException
from app.logginglib import init_custom_logger
from app.schemas.campaign import (
    CampaignDataRequest,
    CampaignDataResponse,
    CampaignFilterOptionsResponse,
    CampaignCountryRegionsResponse,
)
from app.utils import countries_filter

logger = logging.getLogger(__name__)
init_custom_logger(logger)

router = APIRouter(prefix=f"/{ApiPrefix.v1}/campaigns")


@router.post(
    path="/{campaign}/data",
    response_model=CampaignDataResponse,
    status_code=status.HTTP_200_OK,
)
def get_campaign_data(campaign: str, campaign_data_req: CampaignDataRequest):
    """Get campaign data"""

    check_if_campaign_exists(campaign)

    return CampaignDataResponse(data="123")


@router.get(
    path="/{campaign}/filter-options",
    response_model=CampaignFilterOptionsResponse,
    status_code=status.HTTP_200_OK,
)
def get_campaign_filter_options(campaign: str):
    """Get campaign filter options"""

    check_if_campaign_exists(campaign)

    countries = countries_filter.get_unique_countries(campaign=campaign)

    return CampaignFilterOptionsResponse(countries=countries)


@router.get(
    path="/{campaign}/countries/{country}/regions",
    response_model=CampaignCountryRegionsResponse,
    status_code=status.HTTP_200_OK,
)
def get_country_regions(campaign: str, country: str):
    """Get country regions"""

    check_if_campaign_exists(campaign=campaign)
    check_if_country_exists_in_campaign(campaign=campaign, country=country)

    regions = countries_filter.get_country_regions(campaign=campaign, country=country)

    return CampaignCountryRegionsResponse(regions=regions)


def check_if_campaign_exists(campaign: str):
    """
    Check if campaign exists, If not, raise an exception

    :param campaign: The campaign
    """

    if campaign.lower() not in [c.lower() for c in CAMPAIGNS_LIST]:
        raise ResourceNotFoundHTTPException("Campaign not found")


def check_if_country_exists_in_campaign(campaign: str, country: str):
    """
    Check if country exists in campaign, If not, raise an exception

    :param campaign: The campaign
    :param country: The country
    """

    countries = countries_filter.get_unique_countries(campaign=campaign)
    if country.lower() not in [c.lower() for c in countries]:
        raise ResourceNotFoundHTTPException("Country not found")
