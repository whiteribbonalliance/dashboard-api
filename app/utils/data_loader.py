"""
Requests the dataframe of a campaign from BigQuery and stores the data into the databank
"""

import copy
import json
import logging
import os

import numpy as np
import pandas as pd

from app import constants, globals, databank
from app.enums.campaign_code import CampaignCode
from app.enums.question_code import QuestionCode
from app.logginglib import init_custom_logger
from app.schemas.age import Age
from app.schemas.age_range import AgeRange
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
from app.utils import helpers
from app.utils import q_col_names

logger = logging.getLogger(__name__)
init_custom_logger(logger)


def get_parent_category(sub_categories: str, campaign_code: CampaignCode) -> str:
    mapping_to_parent_category = code_hierarchy.get_mapping_code_to_parent_category(
        campaign_code=campaign_code
    )
    categories = [x for x in sub_categories.split("/") if x]
    parent_categories = sorted(
        set([mapping_to_parent_category.get(x, x) for x in categories])
    )

    return "/".join(parent_categories)


def get_age_range(age: str | int | None, campaign_code: CampaignCode) -> str | None:
    """Convert age to an age range e.g. '30' -> '25-34'"""

    if age is None:
        return age

    if isinstance(age, str):
        if age.isnumeric():
            age = int(age)
        else:
            return age  # Non-numeric e.g. 'prefer not to say' or already an age range

    if campaign_code == CampaignCode.healthwellbeing:
        if age >= 65:
            return "65+"
        if age >= 56:
            return "56-64"
        if age >= 46:
            return "46-55"
        if age >= 36:
            return "36-45"
        if age >= 26:
            return "26-35"
        if age >= 21:
            return "21-25"
        if age >= 16:
            return "16-20"
        if age >= 10:
            return "10-15"
    else:
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


def fill_additional_q_columns(
    row: pd.Series, campaign_code: CampaignCode, q_code: QuestionCode
):
    """Fill additional question columns with data from additional_fields"""

    additional_fields = json.loads(row["additional_fields"])

    response_original_text = additional_fields.get(
        f"{q_code.value}_response_original_text"
    )
    response_english_text = additional_fields.get(
        f"{q_code.value}_response_english_text"
    )
    response_lemmatized_text = additional_fields.get(
        f"{q_code.value}_response_lemmatized_text"
    )
    response_nlu_category = additional_fields.get(
        f"{q_code.value}_response_nlu_category"
    )
    response_original_lang = additional_fields.get(
        f"{q_code.value}_response_original_lang"
    )

    # For economic_empowerment_mexico append original_text and english_text
    if campaign_code == CampaignCode.economic_empowerment_mexico:
        if response_original_text and response_english_text:
            row[
                q_col_names.get_raw_response_col_name(q_code=q_code)
            ] = f"{response_original_text} ({response_english_text})"
        elif response_original_text:
            row[
                q_col_names.get_raw_response_col_name(q_code=q_code)
            ] = response_original_text
    else:
        row[
            q_col_names.get_raw_response_col_name(q_code=q_code)
        ] = response_original_text

    if response_lemmatized_text:
        row[
            q_col_names.get_lemmatized_col_name(q_code=q_code)
        ] = response_lemmatized_text
    if response_nlu_category:
        row[
            q_col_names.get_canonical_code_col_name(q_code=q_code)
        ] = response_nlu_category
    if response_original_lang:
        row[
            q_col_names.get_original_language_col_name(q_code=q_code)
        ] = response_original_lang

    return row


def fill_additional_setting_column(row: pd.Series):
    """Fill additional setting column"""

    additional_fields = json.loads(row["additional_fields"])

    setting = additional_fields.get("setting")

    # Only campaign 'healthwellbeing' has additional field 'setting'
    if setting:
        row["setting"] = setting

    return row


def add_additional_fields_columns(
    df: pd.DataFrame, campaign_code: CampaignCode
) -> pd.DataFrame:
    """Add columns from 'additional_fields'"""

    # Q codes available in a campaign
    campaign_q_codes = helpers.get_campaign_q_codes(campaign_code=campaign_code)

    # Create additional column 'setting'
    df["setting"] = ""

    if campaign_code == CampaignCode.healthwellbeing:
        # Fill additional column 'setting'
        df = df.apply(
            lambda x: fill_additional_setting_column(row=x),
            axis=1,
        )

    for q_code in [x for x in campaign_q_codes if x != QuestionCode.q1]:
        # Create additional columns per question
        df[q_col_names.get_raw_response_col_name(q_code=q_code)] = ""
        df[q_col_names.get_lemmatized_col_name(q_code=q_code)] = ""
        df[q_col_names.get_canonical_code_col_name(q_code=q_code)] = ""
        df[q_col_names.get_original_language_col_name(q_code=q_code)] = ""

        # Fill additional columns per question
        df = df.apply(
            lambda x: fill_additional_q_columns(
                row=x, campaign_code=campaign_code, q_code=q_code
            ),
            axis=1,
        )

    return df


def load_campaign_data(campaign_code: CampaignCode):
    """
    Load campaign data

    :param campaign_code: The campaign code
    """

    # Create a copy of the databank to write campaign data to
    # If writing of the data succeeds, then the current databank will be replaced with the databank copy at the end of
    # this function
    # This is to make sure new data loads correctly into the databank
    # If an error occurs while loading new data, then the current databank stays as is and the error is logged
    databank_copy = copy.deepcopy(
        databank.get_campaign_databank(campaign_code=campaign_code)
    )

    # CRUD
    campaign_crud = CampaignCRUD(
        campaign_code=campaign_code, databank_copy=databank_copy
    )

    # Q codes available in a campaign
    campaign_q_codes = helpers.get_campaign_q_codes(campaign_code=campaign_code)

    # Get the dataframe from BigQuery
    df_responses = bigquery_interactions.get_campaign_df_from_bigquery(
        campaign_code=campaign_code
    )

    # Add columns from 'additional_fields'
    df_responses = add_additional_fields_columns(
        df=df_responses, campaign_code=campaign_code
    )

    # Add tokenized column
    for q_code in campaign_q_codes:
        df_responses[q_col_names.get_tokenized_col_name(q_code=q_code)] = df_responses[
            q_col_names.get_lemmatized_col_name(q_code=q_code)
        ].apply(lambda x: x.split(" "))

    # Apply strip function on alpha2 country codes
    df_responses["alpha2country"] = df_responses["alpha2country"].apply(
        lambda x: x.strip()
    )

    # Add canonical_country column
    df_responses["canonical_country"] = df_responses["alpha2country"].map(
        lambda x: constants.COUNTRIES_DATA[x]["name"]
    )

    # Only keep ages 10-24 for what_young_people_want
    if campaign_code == CampaignCode.what_young_people_want:
        df_responses["age"] = df_responses["age"].apply(filter_ages_10_to_24)
        df_responses = df_responses[df_responses["age"].notna()]

    # Set ages
    ages = df_responses["age"].unique().tolist()
    ages = [Age(code=age, name=age) for age in ages if age is not None]
    campaign_crud.set_ages(ages=ages)

    # Age range
    # Note: Campaigns 'what_women_want' and 'midwives_voices' already contain 'age' as a range
    if (
        campaign_code == CampaignCode.what_women_want
        or campaign_code == CampaignCode.midwives_voices
    ):
        df_responses["age_range"] = df_responses["age"]
    else:
        df_responses["age_range"] = df_responses["age"].apply(
            lambda x: get_age_range(age=x, campaign_code=campaign_code)
        )

    # Set age ranges
    age_ranges = df_responses["age_range"].unique().tolist()
    age_ranges = [
        AgeRange(code=age_range, name=age_range)
        for age_range in age_ranges
        if age_range is not None
    ]
    campaign_crud.set_age_ranges(age_ranges=age_ranges)

    # Remove the UNCODABLE responses
    for q_code in campaign_q_codes:
        df_responses = df_responses[
            ~df_responses[q_col_names.get_canonical_code_col_name(q_code=q_code)].isin(
                ["UNCODABLE"]
            )
        ]

    # What Young People Want has a hard coded rewrite of ENVIRONMENT merged with SAFETY.
    if campaign_code == CampaignCode.what_young_people_want:
        _map = {"ENVIRONMENT": "SAFETY"}
        df_responses[
            q_col_names.get_canonical_code_col_name(q_code=QuestionCode.q1)
        ] = df_responses[
            q_col_names.get_canonical_code_col_name(q_code=QuestionCode.q1)
        ].apply(
            lambda x: _map.get(x, x)
        )

    # Rename canonical_code OTHERQUESTIONABLE to NOTRELATED
    for q_code in campaign_q_codes:
        df_responses[
            q_col_names.get_canonical_code_col_name(q_code=q_code)
        ] = df_responses[q_col_names.get_canonical_code_col_name(q_code=q_code)].apply(
            lambda x: "NOTRELATED" if x == "OTHERQUESTIONABLE" else x
        )

    # Add parent_category column
    for q_code in campaign_q_codes:
        df_responses[
            q_col_names.get_parent_category_col_name(q_code=q_code)
        ] = df_responses[q_col_names.get_canonical_code_col_name(q_code=q_code)].apply(
            lambda x: get_parent_category(sub_categories=x, campaign_code=campaign_code)
        )

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
            if not gender:
                continue
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

    # Set databank copy as current databank
    databank.set_campaign_databank(campaign_code=campaign_code, databank=databank_copy)


def load_campaign_ngrams_unfiltered(campaign_code: CampaignCode):
    """Load campaign ngrams unfiltered"""

    campaign_crud = CampaignCRUD(campaign_code=campaign_code)
    campaign_service = CampaignService(campaign_code=campaign_code)

    df = campaign_crud.get_dataframe().copy()

    # Q codes available in a campaign
    campaign_q_codes = helpers.get_campaign_q_codes(campaign_code=campaign_code)

    for q_code in campaign_q_codes:
        (
            unigram_count_dict,
            bigram_count_dict,
            trigram_count_dict,
        ) = campaign_service.generate_ngrams(df=df, q_code=q_code)

        ngrams_unfiltered = {
            "unigram": unigram_count_dict,
            "bigram": bigram_count_dict,
            "trigram": trigram_count_dict,
        }

        campaign_crud.set_ngrams_unfiltered(
            ngrams_unfiltered=ngrams_unfiltered, q_code=q_code
        )


def load_all_campaigns_data():
    """Load all campaigns data"""

    for campaign_code in CampaignCode:
        print(f"INFO:\t  Loading data for campaign {campaign_code.value}...")

        try:
            load_campaign_data(campaign_code=campaign_code)
        except (Exception,):
            logger.exception(
                f"""Error loading data for campaign {campaign_code.value}."""
            )
        else:
            load_campaign_ngrams_unfiltered(campaign_code=campaign_code)


def load_data():
    """Load data"""

    load_all_campaigns_data()

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
    focused_on_country_campaigns_codes = [
        CampaignCode.economic_empowerment_mexico,
        CampaignCode.what_women_want_pakistan,
    ]
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
