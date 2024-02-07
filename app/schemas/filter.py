"""
MIT License

Copyright (c) 2023 World We Want. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

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


class Filter(BaseModel):
    countries: list[str] = Field(description="The selected alpha-2 country codes")
    regions: list[str] = Field(description="The selected regions")
    provinces: list[str] = Field(description="The selected provinces")
    ages: list[str] = Field(description="The selected ages")
    age_buckets: list[str] = Field(description="The selected age buckets")
    genders: list[str] = Field(description="The selected genders")
    years: list[str] = Field(description="The selected years")
    living_settings: list[str] = Field(description="The selected living settings")
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
