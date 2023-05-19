from pydantic import BaseModel, Field

from app.schemas.filter import Filter


class CampaignDataRequest(BaseModel):
    filter_1: Filter = Field(
        None, description="Selected filter options from `Drill down`"
    )
    filter_2: Filter = Field(
        None, description="Selected filter options from `Compare to...`"
    )


class CampaignDataResponse(BaseModel):
    data: str = Field(description="Test data")


class CampaignFilterOptionsResponse(BaseModel):
    countries: list[str] = Field([], description="All respondents countries")


class CampaignCountryRegionsResponse(BaseModel):
    regions: list[str] = Field([], description="The regions of the country")
