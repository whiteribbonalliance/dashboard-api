"""
Requests the dataframe of a campaign from BigQuery and stores the data into the databank
"""

import json
import logging
import os

import numpy as np

from app import constants
from app.enums.campaign_code import CampaignCode
from app.logginglib import init_custom_logger
from app.schemas.age import Age
from app.schemas.country import Country
from app.schemas.gender import Gender
from app.schemas.profession import Profession
from app.schemas.region import Region
from app.services import bigquery_interactions
from app.services import googlemaps_interactions
from app.services.api_cache import ApiCache
from app.services.campaign import CampaignCRUD, CampaignService
from app.services.translations_cache import TranslationsCache
from app.utils import code_hierarchy
from app.utils import globals

logger = logging.getLogger(__name__)
init_custom_logger(logger)


def load_campaign_data(campaign_code: CampaignCode):
    """
    Load campaign data

    :param campaign_code: The campaign code
    """

    campaign_crud = CampaignCRUD(campaign_code=campaign_code)

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

    # Add canonical_country column
    df_responses["canonical_country"] = df_responses["alpha2country"].map(
        lambda x: constants.COUNTRIES_DATA[x]["name"]
    )

    # Only keep ages 10-24 for PMNCH
    if campaign_code == CampaignCode.what_young_people_want:
        df_responses["age"] = df_responses["age"].apply(filter_ages_10_to_24)
        df_responses = df_responses[df_responses["age"].notna()]

    # Modify age into age bucket (skip if PMNCH)
    if campaign_code != CampaignCode.what_young_people_want:
        df_responses["age"] = df_responses["age"].apply(get_age_bucket)

    # Set ages
    ages = df_responses["age"].unique().tolist()
    ages = [Age(code=age, name=age) for age in ages if age is not None]
    campaign_crud.set_ages(ages=ages)

    # Remove the UNCODABLE responses
    df_responses = df_responses[~df_responses["canonical_code"].isin(["UNCODABLE"])]

    # What Young People Want has a hard coded rewrite of ENVIRONMENT merged with SAFETY.
    if campaign_code == CampaignCode.what_young_people_want:
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
        country = constants.COUNTRIES_DATA.get(alpha2_code)
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
            countries[alpha2_code].regions.append(Region(code=region, name=region))

    # Set countries
    campaign_crud.set_countries(countries=countries)

    # Get responses sample column ids
    column_ids = [col["id"] for col in campaign_crud.get_responses_sample_columns()]

    # Set genders
    genders = []
    if "gender" in column_ids:
        for gender in df_responses["gender"].value_counts().index:
            genders.append(Gender(code=gender, name=gender))
    campaign_crud.set_genders(genders=genders)

    # Set professions
    professions = []
    if "profession" in column_ids:
        for profession in df_responses["profession"].value_counts().index:
            professions.append(Profession(code=profession, name=profession))
    campaign_crud.set_professions(professions=professions)

    # Set dataframe
    campaign_crud.set_dataframe(df=df_responses)


def load_campaign_ngrams_unfiltered(campaign_code: CampaignCode):
    """Load campaign ngrams unfiltered"""

    campaign_crud = CampaignCRUD(campaign_code=campaign_code)
    campaign_service = CampaignService(campaign_code=campaign_code)

    df = campaign_crud.get_dataframe()

    (
        unigram_count_dict,
        bigram_count_dict,
        trigram_count_dict,
    ) = campaign_service.generate_ngrams(df=df)

    ngrams_unfiltered = {
        "unigram": unigram_count_dict,
        "bigram": bigram_count_dict,
        "trigram": trigram_count_dict,
    }

    campaign_crud.set_ngrams_unfiltered(ngrams_unfiltered=ngrams_unfiltered)


def load_all_campaigns_data():
    """Load all campaigns data"""

    for campaign_code in CampaignCode:
        print(f"INFO:\t  Loading data for campaign {campaign_code.value}...")
        load_campaign_data(campaign_code=campaign_code)


def load_all_campaigns_ngrams_unfiltered():
    """Load all campaigns ngrams"""

    for campaign_code in CampaignCode:
        print(f"INFO:\t  Loading ngrams cache for campaign {campaign_code.value}...")
        load_campaign_ngrams_unfiltered(campaign_code=campaign_code)


def load_data():
    """Load data"""

    load_all_campaigns_data()
    load_all_campaigns_ngrams_unfiltered()

    # Clear the API cache
    ApiCache().clear_cache()


def load_translations_cache():
    """Load translations cache"""

    print("INFO:\t  Loading translations cache...")

    # Creating the singleton instance will automatically load the cache
    TranslationsCache()


def load_coordinates():
    """Load coordinates"""

    print(f"INFO:\t  Loading coordinates...")

    stage_is_dev = os.getenv("stage", "") == "dev"
    coordinates_json = "coordinates.json"
    new_coordinates_added = False

    if globals.coordinates:
        coordinates = globals.coordinates
    else:
        with open(coordinates_json, "r") as file:
            coordinates: dict = json.loads(file.read())

    # Get new coordinates (if coordinate is not in coordinates.json)
    focused_on_country_campaigns_codes = [CampaignCode.mexico, CampaignCode.pakistan]
    for campaign_code in focused_on_country_campaigns_codes:
        campaign_crud = CampaignCRUD(campaign_code=campaign_code)
        countries = campaign_crud.get_countries_list()

        if len(countries) < 1:
            logger.warning(f"Campaign {campaign_code.value} has no countries")
            continue

        country_alpha2_code = countries[0].alpha2_code
        country_name = countries[0].name
        country_regions = countries[0].regions

        locations = [
            {
                "country_alpha2_code": country_alpha2_code,
                "country_name": country_name,
                "location": region.name,
            }
            for region in country_regions
        ]
        for location in locations:
            location_country_alpha2_code = location["country_alpha2_code"]
            location_country_name = location["country_name"]
            location_name = location["location"]

            # If coordinate already exists, continue
            country_coordinates = coordinates.get(location_country_alpha2_code)
            if country_coordinates and location_name in country_coordinates.keys():
                continue

            # Get coordinate
            coordinate = googlemaps_interactions.get_coordinate(
                location=f"{location_country_name}, {location_name}"
            )

            # Add coordinate to coordinates
            if not coordinates.get(location_country_alpha2_code):
                coordinates[location_country_alpha2_code] = {}
            coordinates[location_country_alpha2_code][location_name] = coordinate

            if not new_coordinates_added:
                new_coordinates_added = True

    # Save coordinates
    if stage_is_dev and new_coordinates_added:
        with open(coordinates_json, "w") as file:
            file.write(json.dumps(coordinates, indent=2))

    globals.coordinates = coordinates
