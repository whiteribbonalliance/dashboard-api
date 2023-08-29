import logging
from datetime import date
from datetime import datetime

from fastapi import Request, Depends

from app import helpers, auth_handler, http_exceptions
from app.logginglib import init_custom_logger
from app.schemas.common_parameters_campaign import CommonParametersCampaign
from app.schemas.common_parameters_campaign_download_url import (
    CommonParametersCampaignDownloadUrl,
)
from app.schemas.common_parameters_campaign_health_check import (
    CommonParametersCampaignHealthCheck,
)
from app.schemas.date_filter import DateFilter

logger = logging.getLogger(__name__)
init_custom_logger(logger)


async def common_parameters_campaign(
    request: Request, campaign: str, q_code: str = "q1", lang: str = "en"
) -> CommonParametersCampaign:
    """Return the common parameters"""

    campaign_code_verified = helpers.check_campaign(campaign=campaign)
    if not campaign_code_verified:
        raise http_exceptions.ResourceNotFoundHTTPException("Campaign not found")

    language_verified = helpers.check_language(lang=lang)

    q_code_verified = helpers.check_q_code_for_campaign(
        q_code=q_code, campaign_code=campaign_code_verified
    )
    if not q_code_verified:
        raise http_exceptions.ResourceNotFoundHTTPException(
            "Campaign does not have the provided q_code"
        )

    return CommonParametersCampaign(
        campaign_code=campaign_code_verified,
        language=language_verified,
        q_code=q_code_verified,
        request=request,
    )


async def common_parameters_campaign_download_url(
    campaign: str,
    username: str = Depends(auth_handler.auth_wrapper_access_token),
    date_filter: DateFilter | None = None,
) -> CommonParametersCampaignDownloadUrl:
    """Return the common parameters"""

    campaign_code_verified = helpers.check_campaign(campaign=campaign)
    if not campaign_code_verified:
        raise http_exceptions.ResourceNotFoundHTTPException("Campaign not found")

    # Parse date
    from_date: date | None = None
    to_date: date | None = None
    try:
        from_date = (
            datetime.strptime(date_filter.from_date, "%Y-%m-%d").date()
            if date_filter and date_filter.from_date
            else None
        )
        to_date = (
            datetime.strptime(date_filter.to_date, "%Y-%m-%d").date()
            if date_filter and date_filter.to_date
            else None
        )
    except ValueError as e:
        logger.warning(f"Could not parse date from date_filter: {str(e)}")

    return CommonParametersCampaignDownloadUrl(
        campaign_code=campaign_code_verified,
        username=username,
        from_date=from_date,
        to_date=to_date,
    )


async def common_parameters_campaign_health_check(
    request: Request, campaign: str
) -> CommonParametersCampaignHealthCheck:
    """Return the common parameters"""

    campaign_code_verified = helpers.check_campaign(campaign=campaign)
    if not campaign_code_verified:
        raise http_exceptions.ResourceNotFoundHTTPException("Campaign not found")

    return CommonParametersCampaignHealthCheck(
        campaign_code=campaign_code_verified, request=request
    )
