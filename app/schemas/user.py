from pydantic import BaseModel

from app.enums.campaign_code import CampaignCode


class UserBase(BaseModel):
    username: str
    campaign_access: list[CampaignCode]


class UserInternal(UserBase):
    password: str
    is_admin: bool = False


class UserResponse(UserBase):
    campaign_access: list[CampaignCode]
