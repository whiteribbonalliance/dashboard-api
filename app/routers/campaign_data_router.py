import logging

from fastapi import APIRouter, HTTPException, status

from app.constants import CAMPAIGNS_LIST
from app.logginglib import init_custom_logger
from app.schemas.requests import CampaignDataRequest
from app.schemas.responses import CampaignDataResponse

logger = logging.getLogger(__name__)
init_custom_logger(logger)

router = APIRouter(prefix="/campaign-data")


@router.post(
    path="/", response_model=CampaignDataResponse, status_code=status.HTTP_200_OK
)
def get_campaign_data(campaign_data_req: CampaignDataRequest):
    """Get campaign data"""

    campaign = campaign_data_req.campaign
    if campaign not in CAMPAIGNS_LIST:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )

    campaign_data_res = CampaignDataResponse(data="123")

    return campaign_data_res
