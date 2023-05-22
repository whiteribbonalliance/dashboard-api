from pydantic import BaseModel, Field

from app.schemas.country import Country
from app.schemas.response_topic import ResponseTopic


class FilterOptions(BaseModel):
    countries: list[Country] = Field(
        default=[], description="All respondents countries"
    )
    response_topics: list[ResponseTopic] = Field(
        default=[], description="All respondents response topics"
    )
