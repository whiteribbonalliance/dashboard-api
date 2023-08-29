from fastapi import Request
from pydantic import BaseModel

from app.enums.campaign_code import CampaignCode


class CommonParametersCampaignHealthCheck(BaseModel):
    campaign_code: CampaignCode
    request: Request | None

    class Config:
        arbitrary_types_allowed = True
