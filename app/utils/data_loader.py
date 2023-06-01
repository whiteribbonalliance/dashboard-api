"""Requests the dataframe of a campaign from BigQuery and stores the data into the databank"""

import logging

import numpy as np

from app.databank import get_campaign_databank
from app.enums.campaign_code import CampaignCode
from app.logginglib import init_custom_logger
from app.schemas.country import Country
from app.services import bigquery_interactions
from app.utils import code_hierarchy
from app.utils import countries_data_loader
from app.utils.data_access_layer import DataAccessLayer

logger = logging.getLogger(__name__)
init_custom_logger(logger)


def load_campaign_data(campaign_code: CampaignCode):
    """
    Load campaign data

    :param campaign_code: The campaign code
    """

    databank = get_campaign_databank(campaign_code=campaign_code)

    def get_top_level(leaf_categories: str) -> str:
        mapping_to_top_level = code_hierarchy.get_mapping_to_top_level(
            campaign_code=campaign_code
        )
        categories = leaf_categories.split("/")
        top_levels = sorted(
            set([mapping_to_top_level.get(cat, cat) for cat in categories])
        )

        return "/".join(top_levels)

    def get_age_bucket(age: str | int | None) -> str | None:
        """Add age to a specific age bucket e.g. 30 -> '25-34'"""

        if age is None:
            return age

        if isinstance(age, str):
            if age.isnumeric():
                age = int(age)
            else:
                # Non-numeric e.g. 'prefer not to say'
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

    def filter_ages_10_to_24(age: str) -> str:
        """Return age if between 10 and 24, else nan"""

        if isinstance(age, str):
            if age.isnumeric():
                age_int = int(age)
                if 10 <= age_int <= 24:
                    return age

        return np.nan

    # Get the dataframe from BigQuery
    df_responses = bigquery_interactions.get_campaign_df_from_bigquery(
        campaign_code=campaign_code
    )

    # Add tokenized column
    df_responses["tokenized"] = df_responses["lemmatized"].apply(lambda x: x.split(" "))

    # Get countries data
    countries_data = countries_data_loader.get_countries_data_list()

    # Add canonical_country column
    df_responses["canonical_country"] = df_responses["alpha2country"].map(
        lambda x: countries_data[x]["name"]
    )

    # Only keep ages 10-24 for PMNCH
    if campaign_code == CampaignCode.what_young_people_want:
        df_responses["age"] = df_responses["age"].apply(filter_ages_10_to_24)
        df_responses = df_responses[df_responses["age"].notna()]

    # Modify ages into age buckets (skip if PMNCH)
    if campaign_code != CampaignCode.what_young_people_want:
        df_responses["age"] = df_responses["age"].apply(get_age_bucket)

    # Set ages
    databank.ages = df_responses["age"].unique().tolist()
    databank.ages = [age for age in databank.ages if age is not None]
    databank.ages.sort()

    # Remove the UNCODABLE responses
    df_responses = df_responses[~df_responses["canonical_code"].isin(["UNCODABLE"])]

    # What Young People Want has a hard coded rewrite of ENVIRONMENT merged with SAFETY.
    if campaign_code == "pmn01a":
        _map = {"ENVIRONMENT": "SAFETY"}
        df_responses["canonical_code"] = df_responses["canonical_code"].apply(
            lambda x: _map.get(x, x)
        )

    # Rename canonical_code OTHERQUESTIONABLE to NOTRELATED
    df_responses["canonical_code"] = df_responses["canonical_code"].apply(
        lambda x: "NOTRELATED" if x == "OTHERQUESTIONABLE" else x
    )

    # Add top_level column
    df_responses["top_level"] = df_responses["canonical_code"].apply(get_top_level)

    # Create countries
    countries = {}
    countries_alpha2_codes = df_responses[["alpha2country"]].drop_duplicates()
    for idx in range(len(countries_alpha2_codes)):
        alpha2_code = countries_alpha2_codes["alpha2country"].iloc[idx]
        country = countries_data.get(alpha2_code)
        if not country:
            logger.warning("Could not find country in countries_data.json")
            continue
        countries[alpha2_code] = Country(
            alpha2_code=alpha2_code,
            name=country.get("name"),
            demonym=country.get("demonym"),
        )

    # Add regions to countries
    unique_canonical_country_region = df_responses[
        ["alpha2country", "region"]
    ].drop_duplicates()
    for idx in range(len(unique_canonical_country_region)):
        alpha2_code = unique_canonical_country_region["alpha2country"].iloc[idx]
        region = unique_canonical_country_region["region"].iloc[idx]
        if region:
            countries[alpha2_code].regions.append(region)

    # Set countries
    databank.countries = countries

    # Get responses sample column ids
    column_ids = [col["id"] for col in databank.responses_sample_columns]

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

    # Set dataframe
    databank.dataframe = df_responses


def load_campaign_ngrams_unfiltered(campaign_code: CampaignCode):
    """Load ngrams unfiltered"""

    dal = DataAccessLayer(campaign_code=campaign_code)
    databank = get_campaign_databank(campaign_code=campaign_code)

    (
        unigram_count_dict,
        bigram_count_dict,
        trigram_count_dict,
    ) = dal.get_n_grams(df=databank.dataframe)

    ngrams_unfiltered = {
        "unigram": unigram_count_dict,
        "bigram": bigram_count_dict,
        "trigram": trigram_count_dict,
    }

    databank.ngrams_unfiltered = ngrams_unfiltered


def load_all_campaigns_data():
    """Load all campaigns data"""

    print(f"\t  Loading data for campaign {CampaignCode.what_women_want}...")
    load_campaign_data(campaign_code=CampaignCode.what_women_want)

    print(f"\t  Loading data for campaign {CampaignCode.what_young_people_want}...")
    load_campaign_data(campaign_code=CampaignCode.what_young_people_want)

    print(f"\t  Loading data for campaign {CampaignCode.midwives_voices}...")
    load_campaign_data(campaign_code=CampaignCode.midwives_voices)

    print(f"\t  Loading campaigns data complete.")


def load_all_campaigns_ngrams_unfiltered():
    """Load all campaigns ngrams"""

    print(f"\t  Loading ngrams for campaign {CampaignCode.what_women_want}...")
    load_campaign_ngrams_unfiltered(campaign_code=CampaignCode.what_women_want)

    print(f"\t  Loading ngrams for campaign {CampaignCode.what_young_people_want}...")
    load_campaign_ngrams_unfiltered(campaign_code=CampaignCode.what_young_people_want)

    print(f"\t  Loading ngrams for campaign {CampaignCode.midwives_voices}...")
    load_campaign_ngrams_unfiltered(campaign_code=CampaignCode.midwives_voices)

    print(f"\t  Loading campaigns ngrams complete.")


# TODO: Task schedule to run every 12 hours
def load_initial_data():
    """Load initial data"""

    load_all_campaigns_data()
    load_all_campaigns_ngrams_unfiltered()
