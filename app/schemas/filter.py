from pydantic import BaseModel, Field


class Filter(BaseModel):
    countries: list[str] = Field(description="The selected alpha-2 country codes")
    regions: list[str] = Field(description="The selected regions")
    ages: list[str] = Field(description="The selected ages")
    genders: list[str] = Field(description="The selected genders")
    professions: list[str] = Field(description="The selected professions")
    response_topics: list[str] = Field(description="The selected response topics")
    only_responses_from_categories: bool = Field(
        description="Responses from categories or any"
    )
    only_multi_word_phrases_containing_filter_term: bool = Field(
        description="Multi-word phrases containing filter term or any"
    )
    keyword_filter: str = Field(description="Filter by keyword")
    keyword_exclude: str = Field(description="Keyword to exclude")
