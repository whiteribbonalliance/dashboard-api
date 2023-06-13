from pydantic import BaseModel

from app.enums.campaign_code import CampaignCode


class CommonParameters(BaseModel):
    campaign_code: CampaignCode
    language: str
