import logging
import os.path
from io import StringIO
from typing import Annotated

import pandas as pd
import requests
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app import databases, auth_handler
from app import http_exceptions
from app.api import dependencies
from app.crud.campaign import CampaignCRUD
from app.enums.campaign_code import CampaignCode
from app.logginglib import init_custom_logger
from app.schemas.campaign import Campaign
from app.schemas.campaign_request import CampaignRequest
from app.schemas.common_parameters_campaign import CommonParametersCampaign
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
async def read_campaign(
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
async def read_filter_options(
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
    path="/{campaign}/who-the-people-are-options",
    response_model=list[dict],
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
async def read_who_the_people_are_options(
    parameters: Annotated[
        CommonParametersCampaign, Depends(dependencies.dep_common_parameters_campaign)
    ]
):
    """Read who the people are options for campaign"""

    campaign_code = parameters.campaign_code
    language = parameters.language

    # Service
    campaign_service = CampaignService(campaign_code=campaign_code, language=language)

    # Who the people are options
    who_the_people_are_options = campaign_service.get_who_the_people_are_options()

    return who_the_people_are_options


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
    cloud_storage_interactions.cleanup()

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

    # CRUD
    crud = CampaignCRUD(campaign_code=campaign_code)

    # Get dataframe
    df = crud.get_dataframe()

    # File name
    csv_filename = f"wra_{campaign_code.value}.csv"

    # Filter by date
    date_format = "%Y_%m_%d"
    if from_date and to_date:
        df = df[
            (df["ingestion_time"].dt.date >= from_date)
            & (df["ingestion_time"].dt.date <= to_date)
        ]
        csv_filename = f"wra_{campaign_code.value}_{from_date.strftime(date_format)}_to_{to_date.strftime(date_format)}.csv"

    # File paths
    csv_filepath = f"/tmp/{csv_filename}"
    creating_csv_filepath = f"/tmp/wra_creating_{csv_filename}"
    cloud_storage_csv_filepath = f"{csv_filename}"

    # Raise exception if df has no data
    if len(df.index) < 1:
        raise http_exceptions.ResourceNotFoundHTTPException("No data found")

    # If file exists in Cloud Storage
    if cloud_storage_interactions.file_exists(filename=cloud_storage_csv_filepath):
        # Get storage url
        url = cloud_storage_interactions.get_file_url(
            filename=cloud_storage_csv_filepath
        )

    # If file does not exist in Cloud Storage
    else:
        if not os.path.isfile(csv_filepath):
            # Create '/tmp' dir (only if 'dev' because this dir already exists when in production if using App Engine)
            if os.getenv("STAGE") == "dev":
                if not os.path.isdir("/tmp"):
                    os.mkdir("/tmp")

            # Cleanup
            if os.path.isfile(creating_csv_filepath):
                os.remove(creating_csv_filepath)

            # Convert date to string
            df["ingestion_time"] = df["ingestion_time"].apply(
                lambda x: x.strftime(date_format) if x else ""
            )

            # Save dataframe to csv file
            df.to_csv(path_or_buf=creating_csv_filepath, index=False, header=True)

            # Rename
            os.rename(src=creating_csv_filepath, dst=csv_filepath)

        # Upload to storage
        cloud_storage_interactions.upload_file(
            source_filename=csv_filepath,
            destination_filename=cloud_storage_csv_filepath,
        )

        # Remove from tmp
        os.remove(csv_filepath)

        # Get storage url
        url = cloud_storage_interactions.get_file_url(
            filename=cloud_storage_csv_filepath
        )

    def iter_file():
        session = requests.Session()
        response = session.get(url=url, stream=True)

        if not response.ok:
            raise http_exceptions.ResourceNotFoundHTTPException("No data found")

        for chunk in response.iter_content(1024 * 1024):
            yield chunk

    return StreamingResponse(
        content=iter_file(),
        media_type="text/csv",
        headers={
            "Content-Type": "text/csv",
            f"Content-Disposition": f"attachment; filename={csv_filename}",
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
    crud = CampaignCRUD(campaign_code=campaign_code)

    # Get dataframe
    df = crud.get_dataframe()

    # Countries breakdown
    df = pd.DataFrame({"count": df.groupby(["canonical_country"]).size()}).reset_index()

    # Raise exception if df has no data
    if len(df.index) < 1:
        raise http_exceptions.ResourceNotFoundHTTPException("No data found")

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
            f"Content-Disposition": f"attachment; filename=wra_{campaign_code.value}_countries_breakdown.csv",
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
    crud = CampaignCRUD(campaign_code=campaign_code)

    # Get dataframe
    df = crud.get_dataframe()

    # Source files breakdown
    df = pd.DataFrame({"count": df.groupby(["data_source"]).size()}).reset_index()

    # Raise exception if df has no data
    if len(df.index) < 1:
        raise http_exceptions.ResourceNotFoundHTTPException("No data found")

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
            f"Content-Disposition": f"attachment; filename=wra_{campaign_code.value}_source_files_breakdown.csv",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
