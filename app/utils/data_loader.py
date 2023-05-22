"""Requests the dataframe of a campaign from BigQuery and stores the data into the databank"""

import json

from pandas import DataFrame

from app.databank import get_campaign_databank
from app.enums.campaigns import Campaigns
from app.schemas.country import Country
from app.services import bigquery_interactions
from app.utils import code_hierarchy


def load_campaign_dataframe(campaign: str) -> DataFrame:
    """
    Get the dataframe of a campaign

    :param campaign: The campaign
    """

    databank = get_campaign_databank(campaign=campaign)

    def get_top_level(leaf_categories):
        mapping_to_top_level = code_hierarchy.get_mapping_to_top_level(
            campaign=campaign
        )
        categories = leaf_categories.split("/")
        top_levels = sorted(
            set([mapping_to_top_level.get(cat, cat) for cat in categories])
        )

        return "/".join(top_levels)

    def get_age_bucket(age: str | int | None):
        """Add age to a specific age bucket e.g. 30 -> '25-34'"""

        if age is None:
            return age

        if isinstance(age, str):
            if age.isnumeric():
                age = int(age)
            else:
                return age

        if age >= 55:
            return "55+"
        if age >= 45:
            return "45-54"
        if age >= 35:
            return "35-44"
        if age >= 25:
            return "25-34"
        if age >= 20:
            return "20-24"
        if age >= 15:
            return "15-19"

        return "N/A"

    # Get the dataframe from BigQuery
    df_responses = bigquery_interactions.get_campaign_df_from_bigquery(
        campaign=campaign
    )

    # Add tokenized column
    df_responses["tokenized"] = df_responses["lemmatized"].apply(lambda x: x.split(" "))

    # Load countries_data.json
    with open("countries_data.json", "r") as countries_data:
        countries_data = json.loads(countries_data.read())

    # Add canonical_country column
    df_responses["canonical_country"] = df_responses["alpha2country"].map(
        lambda x: countries_data[x]["name"]
    )

    # Edit age column
    df_responses["age"] = df_responses["age"].apply(get_age_bucket)

    # Remove the UNCODABLE responses
    df_responses = df_responses[~df_responses["canonical_code"].isin(["UNCODABLE"])]

    # What Young People Want has a hard coded rewrite of ENVIRONMENT merged with SAFETY.
    if campaign == "pmn01a":
        _map = {"ENVIRONMENT": "SAFETY"}
        df_responses["canonical_code"] = df_responses["canonical_code"].apply(
            lambda x: _map.get(x, x)
        )

    # Rename OTHERQUESTIONABLE to NOTRELATED
    df_responses["canonical_code"] = df_responses["canonical_code"].apply(
        lambda x: "NOTRELATED" if x == "OTHERQUESTIONABLE" else x
    )

    # Add top_level column
    df_responses["top_level"] = df_responses["canonical_code"].apply(
        lambda x: get_top_level(leaf_categories=x)
    )

    # Add age_str column
    df_responses["age_str"] = df_responses["age"].apply(
        lambda x: "N/A" if x == 0 else x
    )

    # Create countries
    countries = {}
    countries_alpha2_codes = df_responses[["alpha2country"]].drop_duplicates()
    for idx in range(len(countries_alpha2_codes)):
        alpha2_code = countries_alpha2_codes["alpha2country"].iloc[idx]
        country = countries_data.get(alpha2_code)
        if not country:
            # TODO: Log this
            continue
        countries[alpha2_code] = Country(
            alpha2_code=alpha2_code,
            name=country.get("name"),
            demonym=country.get("demonym"),
        )

    # Add regions to countries
    unique_canonical_country_region = df_responses[
        ["alpha2country", "Region"]
    ].drop_duplicates()
    for idx in range(len(unique_canonical_country_region)):
        alpha2_code = unique_canonical_country_region["alpha2country"].iloc[idx]
        region = unique_canonical_country_region["Region"].iloc[idx]
        if region:
            countries[alpha2_code].regions.append(region)

    # Set countries
    databank.countries = countries

    # Get column ids
    column_ids = [col["id"] for col in databank.excerpt_columns]

    # Set genders
    genders = []
    if "gender" in column_ids:
        for gender in df_responses["gender"].value_counts().index:
            genders.append(gender)
    databank.genders = genders

    # Set professions
    professions = []
    if "professional_title" in column_ids:
        for professional_title in (
            df_responses["professional_title"].value_counts().index
        ):
            professions.append(professional_title)
    databank.professions = professions

    # Only include ages 10-24 for pmnch
    if campaign == Campaigns.what_young_people_want:
        df_responses = df_responses.query(
            "age == '10-14' | age == '15-19' | age == '20-24'"
        )

    # Set dataframe
    databank.dataframe = df_responses

    return df_responses


def load_all_campaigns_dataframes():
    """Load all campaigns dataframes"""

    # print("Loading data for campaign wra03a...")
    load_campaign_dataframe(campaign="wra03a")

    # print("Loading data for campaign pmn01a...")
    # load_campaign_dataframe(campaign="pmn01a")

    # print("Loading data for campaign midwife...")
    # load_campaign_dataframe(campaign="midwife")
