from pydantic import BaseModel, Field


class Filter(BaseModel):
    country: str = Field(None, description="The alpha-2 country code of the respondent")
    region: str = Field(None, description="The region of the respondent")
    age: str = Field(None, description="The age of the respondent")
    gender: str = Field(None, description="The gender of the respondent")
    profession: str = Field(None, description="The profession of the respondent")
    topic: str = Field(None, description="The topic")
    match_categories: bool = Field(None, description="Match categories or not")
    keyword_filter: str = Field(None, description="Filter by keyword")
    keyword_exclude: str = Field(None, description="Keyword to exclude")
