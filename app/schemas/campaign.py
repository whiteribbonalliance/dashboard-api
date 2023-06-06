from pydantic import BaseModel


class Campaign(BaseModel):
    responses_sample: dict
    responses_breakdown: list[dict]
    top_words_and_phrases: dict
    histogram: dict
    filter_1_description: str
    filter_2_description: str
    filter_1_respondents_count: int
    filter_2_respondents_count: int
    filter_1_average_age: str
    filter_2_average_age: str
