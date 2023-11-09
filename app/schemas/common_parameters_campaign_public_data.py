from fastapi import Request
from pydantic import BaseModel

from app.enums.campaign_code import CampaignCode


class CommonParametersCampaignPublicData(BaseModel):
    campaign_code: CampaignCode
    request: Request | None
    response_year: str

    class Config:
        arbitrary_types_allowed = True
