import logging
from datetime import date
from datetime import datetime

from fastapi import Request, Depends

from app import helpers, auth_handler, http_exceptions
from app.crud.campaign import CampaignCRUD
from app.enums.campaign_code import CampaignCode
from app.logginglib import init_custom_logger
from app.schemas.common_parameters_campaign import CommonParametersCampaign
from app.schemas.common_parameters_campaigns_merged import (
    CommonParametersCampaignsMerged,
)
from app.schemas.date_filter import DateFilter
from app.schemas.parameters_campaign_data import (
    ParametersCampaignData,
)

logger = logging.getLogger(__name__)
init_custom_logger(logger)


def dep_campaign_code(
    campaign_code: CampaignCode = Depends(helpers.check_campaign),
):
    """Return the campaign code"""

    if not campaign_code:
        raise http_exceptions.ResourceNotFoundHTTPException("Campaign not found")

    return campaign_code


def dep_common_parameters_campaign(
    request: Request,
    campaign_code: CampaignCode = Depends(dep_campaign_code),
    q_code: str = "q1",
    response_year: str = "",
    lang: str = Depends(helpers.check_language),
) -> CommonParametersCampaign:
    """Return the common parameters"""

    # CRUD
    campaign_crud = CampaignCRUD(campaign_code=campaign_code)

    # Verify q_code
    q_code_verified = None
    for q in campaign_crud.get_q_codes():
        if q.value == q_code:
            q_code_verified = q
            break

    if not q_code_verified:
        raise http_exceptions.ResourceNotFoundHTTPException(
            "Campaign does not have the provided q_code"
        )

    return CommonParametersCampaign(
        campaign_code=campaign_code,
        language=lang,
        q_code=q_code_verified,
        response_year=response_year,
        request=request,
    )


def dep_common_parameters_all_campaigns(
    request: Request,
    lang: str = Depends(helpers.check_language),
) -> CommonParametersCampaignsMerged:
    """Return the common parameters"""

    return CommonParametersCampaignsMerged(
        language=lang,
        request=request,
    )


def dep_parameters_campaign_data(
    campaign_code: CampaignCode = Depends(dep_campaign_code),
    username: str = Depends(auth_handler.auth_wrapper_access_token),
    date_filter: DateFilter | None = None,
) -> ParametersCampaignData:
    """Return the common parameters"""

    date_format = "%Y-%m-%d"

    # Parse date
    from_date: date | None = None
    to_date: date | None = None
    try:
        from_date = (
            datetime.strptime(date_filter.from_date, date_format).date()
            if date_filter and date_filter.from_date
            else None
        )
        to_date = (
            datetime.strptime(date_filter.to_date, date_format).date()
            if date_filter and date_filter.to_date
            else None
        )
    except ValueError as e:
        logger.warning(f"Could not parse date from date_filter: {str(e)}")

    return ParametersCampaignData(
        campaign_code=campaign_code,
        username=username,
        from_date=from_date,
        to_date=to_date,
    )
