from pydantic import BaseModel, Field


class Filter(BaseModel):
    countries: str = Field(
        default=None, description="The selected alpha-2 country codes"
    )
    regions: str = Field(default=None, description="The selected regions")
    age_buckets: str = Field(default=None, description="The selected age buckets")
    genders: str = Field(default=None, description="The selected genders")
    professions: str = Field(default=None, description="The selected professions")
    response_topics: str = Field(
        default=None, description="The selected response topics"
    )
    responses_from_categories_or_any: bool = Field(
        default=False, description="Responses from categories or any"
    )
    keyword_filter: str = Field(default=None, description="Filter by keyword")
    keyword_exclude: str = Field(default=None, description="Keyword to exclude")
    multi_word_phrases_filter_term_or_any: bool = Field(
        default=False, description="Multi-word phrases containing filter term or any"
    )
