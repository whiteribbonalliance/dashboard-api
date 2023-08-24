from typing import Annotated

from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse

import app.api.v1.endpoints.campaigns as api_campaigns
from app.api import dependencies
from app.schemas.campaign_request import CampaignRequest
from app.schemas.common_parameters_health_check import CommonParametersHealthCheck
from app.utils import filters

router = APIRouter(prefix="/health-check")


@router.get(path="", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok"}


@router.get(path="/{campaign}", status_code=status.HTTP_200_OK)
async def health_check(
    common_parameters: Annotated[
        CommonParametersHealthCheck,
        Depends(dependencies.common_parameters_health_check),
    ]
):
    """Health check for campaign"""

    campaign_code = common_parameters.campaign_code
    request = common_parameters.request

    common_parameters_campaigns = await dependencies.common_parameters_campaigns(
        request=request, campaign=campaign_code.value, lang="en"
    )
    campaign_req = CampaignRequest(
        filter_1=filters.get_default_filter(), filter_2=filters.get_default_filter()
    )

    response = await api_campaigns.read_campaign(
        common_parameters=common_parameters_campaigns, campaign_req=campaign_req
    )

    if response:
        return JSONResponse(
            content={"status": "success"}, status_code=status.HTTP_200_OK
        )
    else:
        return JSONResponse(
            content={"status": "error"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
