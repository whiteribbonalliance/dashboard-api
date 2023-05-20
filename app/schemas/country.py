from pydantic import BaseModel, Field


class CountryResponse(BaseModel):
    regions: list[str] = Field([], description="The regions of the country")
