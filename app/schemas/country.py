from pydantic import BaseModel, Field


class CountryResponse(BaseModel):
    regions: list[dict] = Field([], description="The regions of the country")
