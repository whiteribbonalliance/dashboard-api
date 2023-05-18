from pydantic import BaseModel, Field


class FilterOptions(BaseModel):
    country: str = Field(None, description="The alpha-2 country code of the respondent")

    region: str = Field(None, description="The region of the respondent")

    topic: str = Field(None, description="The topic")

    match_categories: bool = Field(None, description="Match categories or show all")

    age: str = Field(None, description="The respondents age")

    gender: str = Field(None, description="The respondents gender")

    profession: str = Field(None, description="The respondents profession")

    keyword_filter: str = Field(None, description="Filter by keyword")

    keyword_exclude: str = Field(None, description="Keyword to exclude")
