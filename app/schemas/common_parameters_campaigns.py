from fastapi import Request
from pydantic import BaseModel

from app.enums.campaign_code import CampaignCode
from app.enums.question_code import QuestionCode


class CommonParametersCampaigns(BaseModel):
    campaign_code: CampaignCode
    language: str
    request: Request
    q_code: QuestionCode

    class Config:
        arbitrary_types_allowed = True
