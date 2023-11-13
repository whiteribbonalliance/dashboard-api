import logging
from io import StringIO
from typing import Annotated

import pandas as pd
import requests
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app import helpers
from app import databases, auth_handler
from app import http_exceptions
from app.api import dependencies
from app.crud.campaign import CampaignCRUD
from app.enums.campaign_code import CampaignCode
from app.logginglib import init_custom_logger
from app.schemas.campaign import Campaign
from app.schemas.campaign_request import CampaignRequest
from app.schemas.common_parameters_campaign import CommonParametersCampaign
from app.schemas.common_parameters_campaign_public_data import (
    CommonParametersCampaignPublicData,
)
from app.schemas.filter_options import FilterOptions
from app.schemas.parameters_campaign_data import (
    ParametersCampaignData,
)
from app.services import cloud_storage_interactions
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
def read_campaign(
    parameters: Annotated[
        CommonParametersCampaign, Depends(dependencies.dep_common_parameters_campaign)
    ],
    campaign_req: CampaignRequest,
):
    """Read a campaign"""

    campaign_code = parameters.campaign_code
    language = parameters.language
    q_code = parameters.q_code
    response_year = parameters.response_year

    filter_1 = campaign_req.filter_1
    filter_2 = campaign_req.filter_2

    # Service
    campaign_service = CampaignService(
        campaign_code=campaign_code,
        response_year=response_year,
        language=language,
        filter_1=filter_1,
        filter_2=filter_2,
    )

    # Campaign
    campaign = campaign_service.get_campaign(q_code=q_code)

    return campaign


@router.get(
    path="/{campaign}/filter-options",
    response_model=FilterOptions,
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
def read_filter_options(
    parameters: Annotated[
        CommonParametersCampaign, Depends(dependencies.dep_common_parameters_campaign)
    ]
):
    """Read filter options for campaign"""

    campaign_code = parameters.campaign_code
    language = parameters.language

    # Service
    campaign_service = CampaignService(campaign_code=campaign_code, language=language)

    # Filter options
    filter_options = campaign_service.get_filter_options()

    return filter_options


@router.get(
    path="/{campaign}/histogram-options",
    response_model=list[dict],
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
def read_histogram_options(
    parameters: Annotated[
        CommonParametersCampaign, Depends(dependencies.dep_common_parameters_campaign)
    ]
):
    """Read histogram options for campaign"""

    campaign_code = parameters.campaign_code
    language = parameters.language

    # Service
    campaign_service = CampaignService(campaign_code=campaign_code, language=language)

    # Histogram options
    histogram_options = campaign_service.get_histogram_options()

    return histogram_options


@router.post(
    path="/{campaign}/data",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
)
def campaign_data(
    parameters: Annotated[
        ParametersCampaignData,
        Depends(dependencies.dep_parameters_campaign_data),
    ]
):
    """Read campaign data"""

    campaign_code = parameters.campaign_code
    username = parameters.username
    from_date = parameters.from_date
    to_date = parameters.to_date

    # Cleanup
    cloud_storage_interactions.cleanup_if_over_5gb()

    # Get user
    users = databases.get_users()
    db_user = users.get(username)
    if not db_user:
        raise http_exceptions.UnauthorizedHTTPException("Unknown user")

    # Check if user has access to campaign
    if campaign_code not in db_user.campaign_access:
        raise http_exceptions.UnauthorizedHTTPException(
            "User has no access to campaign"
        )

    # Service
    campaign_service = CampaignService(campaign_code=campaign_code)

    # Get url and filename
    url, csv_filename = campaign_service.get_campaign_data_url_and_filename(
        from_date=from_date, to_date=to_date
    )

    def iter_file():
        with requests.Session() as session:
            response = session.get(url=url, stream=True)
            response.raise_for_status()
            for chunk in response.iter_content(1024 * 1024):
                yield chunk

    return StreamingResponse(
        content=iter_file(),
        media_type="text/csv",
        headers={
            "Content-Type": "text/csv",
            "Content-Disposition": f"attachment; filename={csv_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.post(
    path="/{campaign}/public/data",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
)
def campaign_public_data(
    parameters: Annotated[
        CommonParametersCampaignPublicData,
        Depends(dependencies.dep_common_parameters_campaign_public_data),
    ],
    campaign_req: CampaignRequest,
):
    """Read campaign public data"""

    campaign_code = parameters.campaign_code
    response_year = parameters.response_year
    filter_1 = campaign_req.filter_1
    filter_2 = campaign_req.filter_2

    # Only allow campaign healthwellbeing
    if campaign_code != CampaignCode.healthwellbeing:
        raise http_exceptions.UnauthorizedHTTPException(
            "Reading campaign data not allowed."
        )

    # Service
    campaign_service = CampaignService(
        campaign_code=campaign_code,
        response_year=response_year,
        language="en",
        filter_1=filter_1,
        filter_2=filter_2,
    )

    # Create unique filename code from filters by hashing the filter objects
    unique_filename_code = ""
    if filter_1:
        unique_filename_code = unique_filename_code + helpers.get_dict_hash_value(
            filter_1.dict()
        )
    if filter_2:
        unique_filename_code = unique_filename_code + helpers.get_dict_hash_value(
            filter_2.dict()
        )

    # Get url and filename
    url, csv_filename = campaign_service.get_campaign_data_url_and_filename(
        unique_filename_code=unique_filename_code
    )

    def iter_file():
        with requests.Session() as session:
            response = session.get(url=url, stream=True)
            response.raise_for_status()
            for chunk in response.iter_content(1024 * 1024):
                yield chunk

    return StreamingResponse(
        content=iter_file(),
        media_type="text/csv",
        headers={
            "Content-Type": "text/csv",
            "Content-Disposition": f"attachment; filename={csv_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.get(
    path="/{campaign}/countries-breakdown",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
)
async def campaign_countries_breakdown(
    campaign_code: Annotated[CampaignCode, Depends(dependencies.dep_campaign_code)],
    _: str = Depends(auth_handler.auth_wrapper_access_token),
):
    """Read campaign countries breakdown"""

    # CRUD
    campaign_crud = CampaignCRUD(campaign_code=campaign_code)

    # Get dataframe
    df = campaign_crud.get_dataframe()

    # Countries breakdown
    df = pd.DataFrame({"count": df.groupby(["canonical_country"]).size()}).reset_index()

    # Sort
    df = df.sort_values(by="count", ascending=False)

    # Rename column
    df = df.rename(columns={"canonical_country": "country"})

    # To csv
    buffer = StringIO()
    df.to_csv(path_or_buf=buffer, index=False, header=True)

    return StreamingResponse(
        content=iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Type": "text/csv",
            "Content-Disposition": f"attachment; filename=wra_{campaign_code.value}_countries_breakdown.csv",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.get(
    path="/{campaign}/source-files-breakdown",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
)
async def campaign_source_files_breakdown(
    campaign_code: Annotated[CampaignCode, Depends(dependencies.dep_campaign_code)],
    _: str = Depends(auth_handler.auth_wrapper_access_token),
):
    """Read campaign source files breakdown"""

    # CRUD
    campaign_crud = CampaignCRUD(campaign_code=campaign_code)

    # Get dataframe
    df = campaign_crud.get_dataframe()

    # Source files breakdown
    df = pd.DataFrame({"count": df.groupby(["data_source"]).size()}).reset_index()

    # Sort
    df = df.sort_values(by="count", ascending=False)

    # To csv
    buffer = StringIO()
    df.to_csv(path_or_buf=buffer, index=False, header=True)

    return StreamingResponse(
        content=iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Type": "text/csv",
            "Content-Disposition": f"attachment; filename=wra_{campaign_code.value}_source_files_breakdown.csv",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
