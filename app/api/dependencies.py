"""
MIT License

Copyright (c) 2023 White Ribbon Alliance. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import logging

from fastapi import Depends

from app import crud
from app import databases
from app import utils, auth_handler, http_exceptions
from app.core.settings import get_settings
from app.helpers.campaigns_config_loader import CAMPAIGNS_CONFIG
from app.logginglib import init_custom_logger
from app.types import TCloudService

settings = get_settings()

logger = logging.getLogger(__name__)
init_custom_logger(logger)


def verify_user(
    username: str = Depends(auth_handler.auth_wrapper_access_token),
):
    """
    Verify user.
    """

    return username


def campaign_code_exists_check(
    campaign_code: str,
):
    """
    Check if campaign code exists.
    """

    if campaign_config := CAMPAIGNS_CONFIG.get(campaign_code):
        if campaign_code == campaign_config.campaign_code:
            return campaign_code

    raise http_exceptions.ResourceNotFoundHTTPException("Campaign not found.")


def q_code_check(
    campaign_code=Depends(campaign_code_exists_check),
    q_code: str = "q1",
) -> str:
    """
    Check qcode.
    """

    # CRUD
    campaign_crud = crud.Campaign(campaign_code=campaign_code)

    # Verify q_code
    for q in campaign_crud.get_q_codes():
        if q == q_code:
            return q_code

    raise http_exceptions.ResourceNotFoundHTTPException(
        "Campaign does not have the provided q_code"
    )


def response_year_check(
    campaign_code=Depends(campaign_code_exists_check),
    response_year: str = "",
) -> str:
    """
    Check response year.
    """

    if response_year == "":
        return ""

    # CRUD
    campaign_crud = crud.Campaign(campaign_code=campaign_code)

    # Response years
    response_years = campaign_crud.get_response_years()
    if not response_years:
        return ""

    # Verify response_year
    for r in campaign_crud.get_response_years():
        if r == response_year:
            return response_year

    raise http_exceptions.ResourceNotFoundHTTPException(
        "Campaign does not have the provided response year"
    )


def language_check(
    lang: str = "en",
) -> str:
    """
    Language check.
    """

    cloud_service: TCloudService = "google"
    if lang not in utils.get_translation_languages(cloud_service=cloud_service):
        lang = "en"

    return lang


def user_is_admin_check(
    username: str = Depends(verify_user),
) -> str:
    """
    Check if user is admin.
    """

    users = databases.get_users_from_databases()
    db_user = users.get(username)
    if not db_user:
        raise http_exceptions.UnauthorizedHTTPException("Unknown user")

    # Check if user is admin
    if not db_user.is_admin:
        raise http_exceptions.UnauthorizedHTTPException("Unauthorized")

    return username


def user_exists_check(
    username: str = Depends(verify_user),
) -> str:
    """
    Check if user exists.
    """

    users = databases.get_users_from_databases()
    db_user = users.get(username)
    if not db_user:
        raise http_exceptions.UnauthorizedHTTPException("Unknown user")

    return username


def google_credentials_included() -> bool:
    """
    Check if Google credentials is included.
    """

    if not settings.GOOGLE_CREDENTIALS_INCLUDED:
        raise http_exceptions.NotAllowedHTTPException("Could not perform this action.")
    if not settings.GOOGLE_CLOUD_STORAGE_BUCKET_NAME:
        raise http_exceptions.NotAllowedHTTPException("Could not perform this action.")

    return True
