from fastapi import Request
from pydantic import BaseModel

from app.enums.campaign_code import CampaignCode


class CommonParametersCampaigns(BaseModel):
    campaign_code: CampaignCode
    language: str
    request: Request

    class Config:
        arbitrary_types_allowed = True
