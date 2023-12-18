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

from fastapi import APIRouter, status, Depends

from app.api import dependencies
from app.helpers.campaigns_config_loader import CAMPAIGNS_CONFIG
from app.http_exceptions import ResourceNotFoundHTTPException
from app.schemas.campaign_config import CampaignConfigResponse

router = APIRouter(prefix="/configurations")


@router.get(
    path="",
    response_model=list[CampaignConfigResponse],
    status_code=status.HTTP_200_OK,
)
def read_all_campaigns_configurations():
    """
    Read all campaigns configurations.
    """

    if configurations := CAMPAIGNS_CONFIG.values():
        return [x for x in configurations]

    return []


@router.get(
    path="/{campaign_code}",
    response_model=CampaignConfigResponse,
    status_code=status.HTTP_200_OK,
)
def read_campaign_configuration(
    campaign_code: str = Depends(dependencies.campaign_code_exists_check),
):
    """
    Read campaign configuration.
    """

    configuration = CAMPAIGNS_CONFIG.get(campaign_code)
    if configuration:
        return configuration

    raise ResourceNotFoundHTTPException("Campaign configuration not found.")
