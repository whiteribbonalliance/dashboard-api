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

from pydantic import BaseModel, Field


class FilterOptions(BaseModel):
    countries: list[dict] = Field(
        default=[], description="Options for respondents countries"
    )
    country_regions: list[dict[str, str | list[dict]]] = Field(
        default=[], description="Options for respondents country's regions"
    )
    country_provinces: list[dict[str, str | list[dict]]] = Field(
        default=[], description="Options for respondents country's provinces"
    )
    response_topics: list[dict] = Field(
        default=[], description="Options for respondents response topics"
    )
    ages: list[dict] = Field(
        default=[], description="Options for unique respondents ages"
    )
    age_buckets: list[dict] = Field(
        default=[],
        description="Options for unique respondents age buckets (might differ from campaign to campaign)",
    )
    age_buckets_default: list[dict] = Field(
        default=[],
        description="Options for unique respondents age buckets (is same for all campaigns)",
    )
    genders: list[dict] = Field(
        default=[], description="Options for respondents genders"
    )
    living_settings: list[dict] = Field(
        default=[], description="Options for respondents living settings"
    )
    professions: list[dict] = Field(
        default=[], description="Options for unique respondents professions"
    )
    only_responses_from_categories: list[dict] = Field(
        default=[],
        description="Options for showing only categories for responses or not",
    )
    only_multi_word_phrases_containing_filter_term: list[dict] = Field(
        default=[],
        description="Options for showing only multi-word phrases containing filter term or not",
    )
