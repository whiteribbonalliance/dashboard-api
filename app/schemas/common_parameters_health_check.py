from fastapi import Request
from pydantic import BaseModel

from app.enums.campaign_code import CampaignCode


class CommonParametersHealthCheck(BaseModel):
    campaign_code: CampaignCode
    request: Request

    class Config:
        arbitrary_types_allowed = True
