from pandas import DataFrame

from app.config import get_campaign_config
from app.constants import COUNTRY_ALPHA_2_TO_NAME
from app.enums.campaigns import Campaigns
from app.services.bigquery_interactions import get_campaign_df_from_bigquery
from app.utils.code_hierarchy import get_mapping_to_top_level


def get_campaign_df(campaign: str) -> DataFrame:
    """
    Get the dataframe of a campaign

    :param campaign: The campaign
    """

    # Get the campaign config
    config = get_campaign_config(campaign)

    country_to_regions = {}
    genders = []
    professions = []
    countries = []

    column_ids = [col["id"] for col in config.columns_to_display_in_excerpt]

    # Get the dataframe from BigQuery
    df_responses = get_campaign_df_from_bigquery(campaign=campaign)

    # Set tokenized column
    df_responses["tokenized"] = df_responses["lemmatized"].apply(lambda x: x.split(" "))

    # Set canonical_country column
    df_responses["canonical_country"] = df_responses.alpha2country.map(
        COUNTRY_ALPHA_2_TO_NAME
    )

    # Remove all countries not present in the data from the countries list.
    config.countries_list = df_responses["alpha2country"].unique().tolist()

    def get_age_bucket(age):
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

    df_responses["age"] = df_responses["age"].apply(get_age_bucket)

    # Remove the UNCODABLE responses
    df_responses = df_responses[~df_responses["canonical_code"].isin(["UNCODABLE"])]

    if campaign == "pmn01a":
        # What Young People Want has a hard coded rewrite of ENVIRONMENT merged with SAFETY.
        _map = {"ENVIRONMENT": "SAFETY"}
        df_responses["canonical_code"] = df_responses["canonical_code"].apply(
            lambda x: _map.get(x, x)
        )

    df_responses["canonical_code"] = df_responses["canonical_code"].apply(
        lambda x: "NOTRELATED" if x == "OTHERQUESTIONABLE" else x
    )

    df_responses["top_level"] = df_responses.canonical_code.apply(
        lambda x: get_top_level(campaign=campaign, leaf_categories=x)
    )

    df_responses["age_str"] = df_responses["age"].apply(
        lambda x: "N/A" if x == 0 else x
    )

    unique_locations = df_responses[["canonical_country", "Region"]].drop_duplicates()
    for idx in range(len(unique_locations)):
        loc = unique_locations.canonical_country.iloc[idx]
        reg = unique_locations.Region.iloc[idx]
        if loc not in country_to_regions:
            country_to_regions[loc] = []
        country_to_regions[loc].append(reg)

    # Set gender
    if "gender" in column_ids:
        for gender in df_responses.gender.value_counts().index:
            genders.append(gender)

    # Set professions
    if "professional_title" in column_ids:
        for professional_title in df_responses.professional_title.value_counts().index:
            professions.append(professional_title)

    for country in df_responses.canonical_country.value_counts().index:
        countries.append(country)

    # Only include ages 10-24 for pmnch
    if campaign == Campaigns.what_young_people_want:
        df_responses = df_responses.query(
            "age == '10-14' | age == '15-19' | age == '20-24'"
        )

    return df_responses


def get_top_level(campaign: str, leaf_categories):
    mapping_to_top_level = get_mapping_to_top_level(campaign=campaign)
    categories = leaf_categories.split("/")
    top_levels = sorted(set([mapping_to_top_level.get(cat, cat) for cat in categories]))

    return "/".join(top_levels)
