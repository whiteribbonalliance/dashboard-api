from pydantic import BaseModel

from app.enums.campaign_code import CampaignCode


class CommonParametersHealthCheck(BaseModel):
    campaign_code: CampaignCode

    class Config:
        arbitrary_types_allowed = True
