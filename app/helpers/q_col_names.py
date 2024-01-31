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
from app.enums.legacy_campaign_code import LegacyCampaignCode


def get_response_col_name(q_code: str) -> str:
    """Get raw response column name"""

    return f"{q_code}_response"


def get_canonical_code_col_name(q_code: str, campaign_code: str | None = None) -> str:
    """Get canonical code column name"""

    if campaign_code == LegacyCampaignCode.dataexchange.value:
        return "canonical_code_data_exchange"
    else:
        return f"{q_code}_canonical_code"


def get_lemmatized_col_name(q_code: str) -> str:
    """Get lemmatized column name"""

    return f"{q_code}_lemmatized"


def get_parent_category_col_name(q_code: str) -> str:
    """Get parent category column name"""

    return f"{q_code}_parent_category"


def get_label_col_name(q_code: str) -> str:
    """Get label column name"""

    return f"{q_code}_label"


def get_count_col_name(q_code: str) -> str:
    """Get count column name"""

    return f"{q_code}_count"


def get_code_col_name(q_code: str) -> str:
    """Get code column name"""

    return f"{q_code}_code"


def get_description_col_name(q_code: str, campaign_code: str | None = None) -> str:
    """Get description column name"""

    if campaign_code == LegacyCampaignCode.dataexchange.value:
        return "description_data_exchange"
    else:
        return f"{q_code}_description"
