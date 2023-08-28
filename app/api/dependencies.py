from fastapi import Request, Depends

from app import helpers, auth_handler
from app.http_exceptions import ResourceNotFoundHTTPException
from app.schemas.common_parameters_campaigns import CommonParametersCampaigns
from app.schemas.common_parameters_campaigns_download import (
    CommonParametersCampaignsDownload,
)
from app.schemas.common_parameters_health_check import CommonParametersHealthCheck


async def common_parameters_campaigns(
    request: Request, campaign: str, q_code: str = "q1", lang: str = "en"
) -> CommonParametersCampaigns:
    """Return the common parameters"""

    campaign_code_verified = helpers.check_campaign(campaign=campaign)
    if not campaign_code_verified:
        raise ResourceNotFoundHTTPException("Campaign not found")

    language_verified = helpers.check_language(lang=lang)

    q_code_verified = helpers.check_q_code_for_campaign(
        q_code=q_code, campaign_code=campaign_code_verified
    )
    if not q_code_verified:
        raise ResourceNotFoundHTTPException(
            "Campaign does not have the provided q_code"
        )

    return CommonParametersCampaigns(
        campaign_code=campaign_code_verified,
        language=language_verified,
        q_code=q_code_verified,
        request=request,
    )


async def common_parameters_campaigns_download(
    campaign: str,
    username: str = Depends(auth_handler.auth_wrapper_access_token),
    from_date: str = "",
    to_date: str = "",
) -> CommonParametersCampaignsDownload:
    """Return the common parameters"""

    campaign_code_verified = helpers.check_campaign(campaign=campaign)
    if not campaign_code_verified:
        raise ResourceNotFoundHTTPException("Campaign not found")

    return CommonParametersCampaignsDownload(
        campaign_code=campaign_code_verified,
        username=username,
        from_date=from_date,
        to_date=to_date,
    )


async def common_parameters_health_check(
    request: Request, campaign: str
) -> CommonParametersHealthCheck:
    """Return the common parameters"""

    campaign_code_verified = helpers.check_campaign(campaign=campaign)
    if not campaign_code_verified:
        raise ResourceNotFoundHTTPException("Campaign not found")

    return CommonParametersHealthCheck(
        campaign_code=campaign_code_verified, request=request
    )
