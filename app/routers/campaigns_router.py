import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.constants import CAMPAIGNS_LIST
from app.enums.api_prefix import ApiPrefix
from app.exceptions import ResourceNotFoundHTTPException
from app.logginglib import init_custom_logger
from app.schemas.campaign import CampaignRequest, Campaign
from app.schemas.country import Country
from app.schemas.filter_options import FilterOptions
from app.utils import data_reader

logger = logging.getLogger(__name__)
init_custom_logger(logger)

router = APIRouter(prefix=f"/{ApiPrefix.v1}/campaigns")


async def common_parameters(campaign: str):
    """Verify a campaign and return the common parameter"""

    verify_campaign(campaign=campaign)

    return {"campaign": campaign}


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

    campaign = commons.get("campaign")

    return Campaign(data="123")


@router.get(
    path="/{campaign}/filter-options",
    response_model=FilterOptions,
    status_code=status.HTTP_200_OK,
)
async def read_filter_options(commons: Annotated[dict, Depends(common_parameters)]):
    """Read filter options"""

    campaign = commons.get("campaign")

    countries = data_reader.get_countries_list(campaign=campaign)
    response_topics = data_reader.get_response_topics(campaign=campaign)
    age_buckets = data_reader.get_age_buckets(campaign=campaign)
    genders = data_reader.get_genders(campaign=campaign)
    professions = data_reader.get_professions(campaign=campaign)

    return FilterOptions(
        countries=countries,
        response_topics=response_topics,
        age_buckets=age_buckets,
        genders=genders,
        professions=professions,
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

    campaign = commons.get("campaign")
    verify_country(campaign=campaign, country_alpha2_code=country_alpha2_code)

    countries = data_reader.get_countries_dict(campaign=campaign)
    country = countries.get(country_alpha2_code)

    return country


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

    countries = data_reader.get_countries_dict(campaign=campaign)
    country = countries.get(country_alpha2_code)
    if not country:
        raise ResourceNotFoundHTTPException("Country not found")

    return True
