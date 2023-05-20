from pydantic import BaseModel, Field


class FilterOptionsResponse(BaseModel):
    countries: list[dict] = Field([], description="All respondents countries")
    response_topics: list[dict] = Field(
        [], description="All respondents response topics"
    )
