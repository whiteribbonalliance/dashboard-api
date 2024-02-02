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

import os

from pandas import DataFrame
from pydantic import BaseModel

from app.core.settings import get_settings
from app.enums.legacy_campaign_code import LegacyCampaignCode
from app.helpers.campaigns_config_loader import CAMPAIGNS_CONFIG
from app.schemas.category import ParentCategory
from app.schemas.country import Country
from app.schemas.response_column import ResponseSampleColumn
from app.schemas.user import UserInternal

settings = get_settings()


class Database(BaseModel):
    """
    Stores data related to a campaign in memory.
    """

    dataframe: DataFrame = DataFrame(
        columns=[
            "q1_response",
            "q1_canonical_code",
            "q1_lemmatized",
            "q1_parent_category",
            "canonical_country",
            "alpha2country",
            "region",
            "province",
            "age",
            "age_bucket",
            "age_bucket_default",
            "gender",
            "ingestion_time",
            "data_source",
            "profession",
            "setting",
            "response_year",
        ]
    )  # A dummy empty dataframe with possible column names
    q_codes: list[str] = []
    response_years: list[str] = []
    respondent_noun_singular: str
    countries: dict[str, Country] = {}
    genders: list[str] = []
    living_settings: list[str] = []
    professions: list[str] = []
    ages: list[str] = []
    age_buckets: list[str] = []
    age_buckets_default: list[str] = []
    responses_sample_columns: list[ResponseSampleColumn]
    parent_categories: list[ParentCategory]
    ngrams_unfiltered: dict[str, dict[str, dict[str, int]]] = {}
    user: UserInternal | None = None

    class Config:
        arbitrary_types_allowed = True


databases_dict: dict[str, Database] = {}


def create_databases(campaign_codes: list[str]):
    """
    Create in-memory databases.
    """

    # Responses sample columns
    response_col = ResponseSampleColumn(name="Response", id="response")
    topic_col = ResponseSampleColumn(name="Topic(s)", id="description")
    country_col = ResponseSampleColumn(
        name="Country",
        id="canonical_country",
    )
    region_col = ResponseSampleColumn(name="Region", id="region")
    gender_col = ResponseSampleColumn(
        name="Gender",
        id="gender",
    )
    age_col = ResponseSampleColumn(
        name="Age",
        id="age",
    )
    age_bucket_col = ResponseSampleColumn(name="Age", id="age_bucket")
    profession_col = ResponseSampleColumn(name="Professional Title", id="profession")
    year_col = ResponseSampleColumn(name="Year", id="response_year")

    for campaign_code in campaign_codes:
        campaign_config = CAMPAIGNS_CONFIG.get(campaign_code)

        # Responses sample columns
        if campaign_code == LegacyCampaignCode.pmn01a.value:
            responses_sample_columns = [
                response_col,
                topic_col,
                country_col,
                region_col,
                gender_col,
                age_col,
            ]
        elif campaign_code == LegacyCampaignCode.midwife.value:
            responses_sample_columns = [
                response_col,
                topic_col,
                country_col,
                region_col,
                gender_col,
                profession_col,
                age_bucket_col,
            ]
        elif campaign_code == LegacyCampaignCode.wra03a:
            responses_sample_columns = [
                response_col,
                topic_col,
                country_col,
                age_bucket_col,
            ]
        elif campaign_code == LegacyCampaignCode.dataexchange.value:
            # Rename
            topic_col_modified = topic_col.copy()
            topic_col_modified.name = "Topic"

            responses_sample_columns = [
                response_col,
                year_col,
                topic_col_modified,
                country_col,
                age_col,
            ]
        else:
            responses_sample_columns = [
                response_col,
                topic_col,
                country_col,
                age_col,
            ]

        databases_dict[campaign_code] = Database(
            user=UserInternal(
                username=campaign_code,
                password=os.getenv(f"{campaign_code.upper()}_PASSWORD", ""),
                campaign_access=[campaign_code],
                is_admin=False,
            ),
            respondent_noun_singular=campaign_config.respondent_noun_singular,
            responses_sample_columns=responses_sample_columns,
            parent_categories=campaign_config.parent_categories,
        )


def get_campaign_db(campaign_code: str) -> Database | None:
    """
    Get campaign db.
    """

    db = databases_dict.get(campaign_code)
    if db:
        return db


def set_campaign_db(campaign_code: str, db: Database):
    """
    Set campaign db.
    """

    databases_dict[campaign_code] = db


def get_users_from_databases() -> dict[str, UserInternal]:
    """
    Get users.
    """

    users: dict[str, UserInternal] = {}
    for db in databases_dict.values():
        if db.user:
            users[db.user.username] = db.user

    if os.getenv("ADMIN_PASSWORD"):
        admin = UserInternal(
            username="admin",
            password=os.getenv("ADMIN_PASSWORD", ""),
            campaign_access=[x.campaign_code for x in CAMPAIGNS_CONFIG.values()],
            is_admin=True,
        )

        users[admin.username] = admin

    return users
