from typing import Annotated

from fastapi import APIRouter, status, Depends

# import app.api.v1.endpoints.campaigns as api_campaigns
from app.api import dependencies
from app.schemas.common_parameters_health_check import CommonParametersHealthCheck

router = APIRouter(prefix="/health-check")


@router.get(path="", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok"}


@router.get(path="/{campaign}", status_code=status.HTTP_200_OK)
def health_check(
    common_parameters: Annotated[
        CommonParametersHealthCheck,
        Depends(dependencies.common_parameters_health_check),
    ]
):
    campaign_code = common_parameters.campaign_code

    return {"status": campaign_code}
