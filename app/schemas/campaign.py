from pydantic import BaseModel, Field

from app.schemas.filter import Filter


class CampaignRequest(BaseModel):
    filter_1: Filter = Field(
        None, description="Selected filter options from `Drill down`"
    )
    filter_2: Filter = Field(
        None, description="Selected filter options from `Compare to...`"
    )


class CampaignResponse(BaseModel):
    data: str = Field(description="Test data")
