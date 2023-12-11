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

from app import databases
from app import helpers, auth_handler, http_exceptions
from app.crud.campaign import CampaignCRUD
from app.enums.question_code import QuestionCode
from app.logginglib import init_custom_logger
from app.types import CloudService
from app.utils.campaigns_config_loader import CAMPAIGNS_CONFIG

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

    if campaign_code.lower() in [x["code"].lower() for x in CAMPAIGNS_CONFIG]:
        for campaign_config in CAMPAIGNS_CONFIG:
            campaign_code = campaign_config["code"]
            if campaign_code == campaign_code:
                return campaign_code

    raise http_exceptions.ResourceNotFoundHTTPException("Campaign not found.")


def q_code_check(
    campaign_code=Depends(campaign_code_exists_check),
    q_code: str = "q1",
) -> QuestionCode:
    """
    Check qcode.
    """

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

    return q_code_verified


def language_check(
    lang: str = "en",
) -> str:
    """
    Language check.
    """

    cloud_service: CloudService = "google"
    if lang not in helpers.get_translation_languages(cloud_service=cloud_service):
        lang = "en"

    return lang


def user_is_admin_check(
    username: str = Depends(verify_user),
) -> str:
    """
    Check if user is admin.
    """

    users = databases.get_users()
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

    users = databases.get_users()
    db_user = users.get(username)
    if not db_user:
        raise http_exceptions.UnauthorizedHTTPException("Unknown user")

    return username
