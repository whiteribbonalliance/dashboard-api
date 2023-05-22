from pydantic import BaseModel, Field


class Filter(BaseModel):
    country: str = Field(
        default=None, description="The alpha-2 country code of the respondent"
    )
    region: str = Field(default=None, description="The region of the respondent")
    age: str = Field(default=None, description="The age of the respondent")
    gender: str = Field(default=None, description="The gender of the respondent")
    profession: str = Field(
        default=None, description="The profession of the respondent"
    )
    response_topic: str = Field(default=None, description="The response topic")
    match_categories: bool = Field(default=None, description="Match categories or not")
    keyword_filter: str = Field(default=None, description="Filter by keyword")
    keyword_exclude: str = Field(default=None, description="Keyword to exclude")
