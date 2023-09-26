from pydantic import BaseModel


class Campaign(BaseModel):
    campaign_code: str
    q_code: str
    all_q_codes: list[str]
    included_response_years: list[str]
    all_response_years: list[str]
    responses_sample: dict
    responses_breakdown: list
    living_settings_breakdown: list
    top_words_and_phrases: dict
    histogram: dict
    genders_breakdown: list[dict]
    world_bubble_maps_coordinates: dict
    list_of_ages_1: list[str] = []
    list_of_ages_2: list[str] = []
    list_of_age_buckets_1: list[str] = []
    list_of_age_buckets_2: list[str] = []
    filter_1_respondents_count: int
    filter_2_respondents_count: int
    filter_1_average_age: str
    filter_2_average_age: str
    filter_1_average_age_bucket: str
    filter_2_average_age_bucket: str
    filter_1_description: str
    filter_2_description: str
    filters_are_identical: bool
