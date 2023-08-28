from pydantic import BaseModel

from app.enums.campaign_code import CampaignCode


class CommonParametersCampaignsDownload(BaseModel):
    campaign_code: CampaignCode
    username: str
    from_date: str
    to_date: str

    class Config:
        arbitrary_types_allowed = True
