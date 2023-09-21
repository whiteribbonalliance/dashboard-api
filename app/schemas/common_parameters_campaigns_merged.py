from fastapi import Request
from pydantic import BaseModel


class CommonParametersCampaignsMerged(BaseModel):
    language: str
    request: Request | None

    class Config:
        arbitrary_types_allowed = True
