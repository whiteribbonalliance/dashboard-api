from pydantic import BaseModel


class Campaign(BaseModel):
    responses_sample: dict
    responses_breakdown: list
    living_settings_breakdown: list
    top_words_and_phrases: dict
    histogram: dict
    genders_breakdown: list[dict]
    world_bubble_maps_coordinates: dict
    filter_1_respondents_count: int
    filter_2_respondents_count: int
    filter_1_average_age: str
    filter_2_average_age: str
    filter_1_description: str
    filter_2_description: str
    filters_are_identical: bool
