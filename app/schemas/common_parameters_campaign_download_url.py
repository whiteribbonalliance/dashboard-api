from datetime import date

from pydantic import BaseModel

from app.enums.campaign_code import CampaignCode


class CommonParametersCampaignDownloadUrl(BaseModel):
    campaign_code: CampaignCode
    username: str
    from_date: date | None
    to_date: date | None

    class Config:
        arbitrary_types_allowed = True
