from pydantic import BaseModel, Field


class CampaignDataResponse(BaseModel):
    data: str = Field(description="Test data")

    class Config:
        orm_mode = True
