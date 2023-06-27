from typing import Optional

from fastapi import Request
from pydantic import BaseModel

from app.enums.campaign_code import CampaignCode


class CommonParameters(BaseModel):
    campaign_code: CampaignCode
    language: str
    request: Request | None

    class Config:
        arbitrary_types_allowed = True
