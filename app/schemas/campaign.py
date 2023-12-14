"""
MIT License

Copyright (c) 2023 White Ribbon Alliance. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

from pydantic import BaseModel


class Campaign(BaseModel):
    campaign_code: str
    current_question: dict
    all_questions: list[dict]
    current_response_years: list[str]
    all_response_years: list[str]
    responses_sample: dict
    responses_breakdown: dict
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
