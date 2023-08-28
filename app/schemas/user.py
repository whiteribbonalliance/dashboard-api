from pydantic import BaseModel

from app.enums.campaign_code import CampaignCode


class User(BaseModel):
    username: str
    password: str
    campaign_access: list[CampaignCode]
