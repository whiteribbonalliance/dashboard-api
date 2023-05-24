from pydantic import BaseModel, Field


class FilterOptions(BaseModel):
    countries: list[dict[str, str]] = Field(
        default=[], description="All respondents countries"
    )
    response_topics: list[dict[str, str]] = Field(
        default=[], description="All respondents response topics"
    )
    age_buckets: list[dict[str, str]] = Field(
        default=[], description="All unique respondents age buckets"
    )
    genders: list[dict[str, str]] = Field(
        default=[], description="All unique respondents genders"
    )
    professions: list[dict[str, str]] = Field(
        default=[], description="All unique respondents professions"
    )
