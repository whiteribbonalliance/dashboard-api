from pydantic import BaseModel, Field


class Filter(BaseModel):
    countries: list[str] = Field(
        default=None, description="The selected alpha-2 country codes"
    )
    regions: list[str] = Field(default=None, description="The selected regions")
    age_buckets: list[str] = Field(default=None, description="The selected age buckets")
    genders: list[str] = Field(default=None, description="The selected genders")
    professions: list[str] = Field(default=None, description="The selected professions")
    response_topics: list[str] = Field(
        default=None, description="The selected response topics"
    )
    only_responses_from_categories: bool = Field(
        default=False, description="Responses from categories or any"
    )
    only_multi_word_phrases_containing_filter_term: bool = Field(
        default=False, description="Multi-word phrases containing filter term or any"
    )
    keyword_filter: str = Field(default=None, description="Filter by keyword")
    keyword_exclude: str = Field(default=None, description="Keyword to exclude")
