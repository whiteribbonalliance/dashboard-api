from pydantic import BaseModel, Field


class FilterOptions(BaseModel):
    countries: list[dict[str, str]] = Field(
        default=[], description="Options for respondents countries"
    )
    country_regions: list[dict[str, list | str]] = Field(
        default=[], description="Options for respondents country's regions"
    )
    response_topics: list[dict[str, str]] = Field(
        default=[], description="Options for respondents response topics"
    )
    ages: list[dict[str, str]] = Field(
        default=[], description="Options for unique respondents ages"
    )
    genders: list[dict[str, str]] = Field(
        default=[], description="Options for respondents genders"
    )
    professions: list[dict[str, str]] = Field(
        default=[], description="Options for unique respondents professions"
    )
    only_responses_from_categories: list[dict[str, bool | str]] = Field(
        default=[],
        description="Options for showing only categories for responses or not",
    )
    only_multi_word_phrases_containing_filter_term: list[dict[str, bool | str]] = Field(
        default=[],
        description="Options for showing only multi-word phrases containing filter term or not",
    )
