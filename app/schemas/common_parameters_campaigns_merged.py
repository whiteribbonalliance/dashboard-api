from fastapi import Request
from pydantic import BaseModel

from app.enums.question_code import QuestionCode


class CommonParametersCampaignsMerged(BaseModel):
    language: str
    request: Request | None
    q_code: QuestionCode

    class Config:
        arbitrary_types_allowed = True
