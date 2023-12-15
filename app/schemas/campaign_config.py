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

import validators
from pydantic import BaseModel, Field, validator

from app.schemas.category import ParentCategory


class CampaignConfig(BaseModel):
    code: str = Field(min_length=1)
    file: str = Field()
    link: str = Field()
    questions: dict[str, str]
    filepath: str = ""
    parent_categories: list[ParentCategory]

    @validator("file", pre=True)
    def file_check(cls, v):
        if v == "":
            return v

        if not v.endswith(".csv"):
            return None

        return v

    @validator("link", pre=True)
    def link_check(cls, v):
        if v == "":
            return v

        if not validators.url(v):
            return None

        return v

    @validator("questions", pre=True)
    def question_check(cls, v):
        for key, value in v.items():
            if not key.startswith("q"):
                return None
            if not key.replace("q", "", 1).isnumeric():
                return None

        return v
