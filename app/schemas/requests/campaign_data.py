from pydantic import BaseModel, Field

from app.schemas.filter_options import FilterOptions


class CampaignDataRequest(BaseModel):
    campaign: str = Field(description="The campaign")

    filter_1: FilterOptions = Field(description="Filter options from `Drill down`")

    filter_2: FilterOptions = Field(description="Filter options from `Compare to...`")
