from pandas import DataFrame

from app.config import get_campaign_config
from app.constants import COUNTRY_ALPHA_2_TO_NAME
from app.enums.campaigns import Campaigns
from app.services.bigquery_interactions import get_campaign_df_from_bigquery
from app.utils.code_hierarchy import get_mapping_to_top_level

# Campaign dataframes
df_wra03a = None
df_pmn01a = None
df_midwife = None


def get_campaign_df(campaign: str) -> DataFrame:
    """
    Get the dataframe of a campaign

    :param campaign: The campaign
    """

    def get_top_level(leaf_categories):
        mapping_to_top_level = get_mapping_to_top_level(campaign=campaign)
        categories = leaf_categories.split("/")
        top_levels = sorted(
            set([mapping_to_top_level.get(cat, cat) for cat in categories])
        )

        return "/".join(top_levels)

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

    config = get_campaign_config(campaign)

    column_ids = [col["id"] for col in config.columns_to_display_in_excerpt]

    # Get the dataframe from BigQuery
    df_responses = get_campaign_df_from_bigquery(campaign=campaign)

    # Set tokenized column
    df_responses["tokenized"] = df_responses["lemmatized"].apply(lambda x: x.split(" "))

    # Set canonical_country column
    df_responses["canonical_country"] = df_responses.alpha2country.map(
        COUNTRY_ALPHA_2_TO_NAME
    )

    # Remove all countries not present in the data from the countries list
    alpha2countries_from_df = df_responses["alpha2country"].unique().tolist()
    new_countries_list = []
    for alpha2code, country_name, demonym in config.countries_list:
        if alpha2code not in alpha2countries_from_df:
            continue
        new_countries_list.append((alpha2code, country_name, demonym))
    config.countries_list = new_countries_list

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
        lambda x: get_top_level(leaf_categories=x)
    )

    df_responses["age_str"] = df_responses["age"].apply(
        lambda x: "N/A" if x == 0 else x
    )

    # Set country to regions dict
    country_to_regions = {}
    unique_canonical_country_region = df_responses[
        ["alpha2country", "canonical_country", "Region"]
    ].drop_duplicates()
    for idx in range(len(unique_canonical_country_region)):
        country_alpha2_code = unique_canonical_country_region.alpha2country.iloc[idx]
        region = unique_canonical_country_region.Region.iloc[idx]
        if country_alpha2_code not in country_to_regions:
            country_to_regions[country_alpha2_code] = []
        if region:
            country_to_regions[country_alpha2_code].append(region)
    config.country_to_regions = country_to_regions

    # Set genders
    genders = []
    if "gender" in column_ids:
        for gender in df_responses.gender.value_counts().index:
            genders.append(gender)
    config.genders = genders

    # Set professions
    professions = []
    if "professional_title" in column_ids:
        for professional_title in df_responses.professional_title.value_counts().index:
            professions.append(professional_title)
    config.professions = professions

    # Set countries
    countries = []
    for country in df_responses.canonical_country.value_counts().index:
        countries.append(country)

    # Only include ages 10-24 for pmnch
    if campaign == Campaigns.what_young_people_want:
        df_responses = df_responses.query(
            "age == '10-14' | age == '15-19' | age == '20-24'"
        )

    return df_responses


def load_campaigns_dataframes():
    """Load campaign dataframes"""

    # print("Loading data for campaign wra03a...")
    global df_wra03a
    df_wra03a = get_campaign_df(campaign="wra03a")

    # print("Loading data for campaign pmn01a...")
    global df_pmn01a
    df_pmn01a = get_campaign_df(campaign="pmn01a")

    # print("Loading data for campaign midwife...")
    global df_midwife
    df_midwife = get_campaign_df(campaign="midwife")
