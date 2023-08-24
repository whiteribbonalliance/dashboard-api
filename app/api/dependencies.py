from fastapi import Request

from app import helpers
from app.http_exceptions import ResourceNotFoundHTTPException
from app.schemas.common_parameters_campaigns import CommonParametersCampaigns
from app.schemas.common_parameters_health_check import CommonParametersHealthCheck


async def common_parameters_campaigns(
    request: Request, campaign: str, lang: str = "en"
) -> CommonParametersCampaigns:
    """Return the common parameters"""

    campaign_code_verified = helpers.check_campaign(campaign=campaign)
    if not campaign_code_verified:
        raise ResourceNotFoundHTTPException("Campaign not found")

    language_verified = helpers.check_language(lang=lang)

    return CommonParametersCampaigns(
        campaign_code=campaign_code_verified,
        language=language_verified,
        request=request,
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
