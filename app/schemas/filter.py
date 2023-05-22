from pydantic import BaseModel, Field


class Filter(BaseModel):
    country: str = Field(
        default=None, description="The selected alpha-2 country code of the respondent"
    )
    region: str = Field(
        default=None, description="The selected region of the respondent"
    )
    age: str = Field(default=None, description="The selected age of the respondent")
    gender: str = Field(
        default=None, description="The selected gender of the respondent"
    )
    profession: str = Field(
        default=None, description="The selected profession of the respondent"
    )
    response_topic: str = Field(default=None, description="The selected response topic")
    only_show_responses_categories: bool = Field(
        default=False, description="Responses from categories or any"
    )
    keyword_filter: str = Field(default=None, description="Filter by keyword")
    keyword_exclude: str = Field(default=None, description="Keyword to exclude")
    only_show_multi_word_phrases_containing_filter_term: bool = Field(
        default=False, description="Multi-word phrases containing filter term or any"
    )
