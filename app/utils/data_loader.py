"""
Requests the dataframe of a campaign from BigQuery and stores the data into the database
"""

import copy
import json
import logging
import os

import numpy as np
import pandas as pd

from app import constants, databases
from app import global_variables
from app.enums.campaign_code import CampaignCode
from app.enums.question_code import QuestionCode
from app.logginglib import init_custom_logger
from app.schemas.age import Age
from app.schemas.age_bucket import AgeBucket
from app.schemas.country import Country
from app.schemas.gender import Gender
from app.schemas.profession import Profession
from app.schemas.region import Region
from app.services import bigquery_interactions
from app.services import cloud_storage_interactions
from app.services import googlemaps_interactions
from app.services.api_cache import ApiCache
from app.services.campaign import CampaignCRUD, CampaignService
from app.services.translations_cache import TranslationsCache
from app.utils import code_hierarchy
from app.utils import q_col_names

logger = logging.getLogger(__name__)
init_custom_logger(logger)


def get_parent_category(sub_categories: str, campaign_code: CampaignCode) -> str:
    """Get parent category"""

    mapping_to_parent_category = code_hierarchy.get_mapping_code_to_parent_category(
        campaign_code=campaign_code
    )
    categories = [x.strip() for x in sub_categories.split("/") if x]
    parent_categories = sorted(
        set([mapping_to_parent_category.get(x, x) for x in categories])
    )

    return "/".join(parent_categories)


def get_age_bucket(
    age: str | int | None, campaign_code: CampaignCode = None
) -> str | None:
    """Convert age to an age bucket e.g. '30' to '25-34'"""

    if age is None:
        return age

    if isinstance(age, str):
        if age.isnumeric():
            age = int(age)
        else:
            return age  # Non-numeric e.g. 'prefer not to say' or already an age bucket

    if campaign_code == CampaignCode.healthwellbeing:
        if age >= 65:
            return "65+"
        if age >= 55:
            return "55-64"
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
        if age >= 10:
            return "10-14"
        if age >= 0:
            return "< 10"
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


def create_additional_q_columns(
    df: pd.DataFrame,
    campaign_code: CampaignCode,
    crud: CampaignCRUD,
) -> pd.DataFrame:
    """Create additional columns (q1_, q2_ etc.) from 'additional_fields'"""

    # Q codes available in a campaign
    campaign_q_codes = crud.get_q_codes()

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


def fill_additional_q_columns(
    row: pd.Series, campaign_code: CampaignCode, q_code: QuestionCode
):
    """Fill additional columns (q1_, q2_ etc.) from 'additional_fields'"""

    # 'additional_fields' can contain the response fields for q2, q3 etc.
    additional_fields = json.loads(row.get("additional_fields", "{}"))

    # If 'healthwellbeing' use the field 'issue' as the text at q2, other columns will use q1 by default
    if campaign_code == CampaignCode.healthwellbeing and q_code == QuestionCode.q2:
        # Get issue
        issue = (
            str(additional_fields.get("issue")).capitalize()
            if additional_fields.get("issue")
            else ""
        )

        response_original_text = issue
        response_english_text = issue
        response_lemmatized_text = issue
        response_nlu_category = row.get("q1_canonical_code", "")
        response_original_lang = row.get("q1_original_language", "")
    else:
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

    # For 'economic_empowerment_mexico' append 'original_text' and 'english_text'
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


def extract_province_from_region(region: str) -> str:
    """Extract province from region"""

    if not region:
        return ""

    region_name_split = region.split(",")
    if len(region_name_split) == 2:
        province = region_name_split[-1].strip()

        return province
    else:
        return ""


def load_campaign_data(campaign_code: CampaignCode):
    """
    Load campaign data

    :param campaign_code: The campaign code
    """

    # Create a tmp copy of the db to write campaign data to
    # If writing of the data succeeds, then the current db will be replaced with the tmp db at the end of this function
    # This is to make sure new data loads correctly into the db
    # If an error occurs while loading new data, then the current db stays as is and the error is logged
    db_tmp = copy.deepcopy(databases.get_campaign_db(campaign_code=campaign_code))

    # CRUD
    campaign_crud = CampaignCRUD(campaign_code=campaign_code, db=db_tmp)

    # Q codes available in a campaign
    campaign_q_codes = campaign_crud.get_q_codes()

    # Get the dataframe from BigQuery
    df_responses = bigquery_interactions.get_campaign_df_from_bigquery(
        campaign_code=campaign_code
    )

    # Create additional q columns (q1_, q2_, etc.)
    df_responses = create_additional_q_columns(
        df=df_responses, campaign_code=campaign_code, crud=campaign_crud
    )

    # Drop 'additional_fields'
    df_responses = df_responses.drop("additional_fields", axis=1)

    # Add tokenized column
    for q_code in campaign_q_codes:
        df_responses[q_col_names.get_tokenized_col_name(q_code=q_code)] = df_responses[
            q_col_names.get_lemmatized_col_name(q_code=q_code)
        ].apply(lambda x: str(x).split(" ") if x else x)

    # Make sure the setting value 'prefer not to say' always starts with a capital letter
    df_responses["setting"] = df_responses["setting"].apply(
        lambda x: x.capitalize() if x and x.lower() == "prefer not to say" else x
    )

    # Apply strip function on alpha2 country codes and make sure the value is uppercase
    df_responses["alpha2country"] = df_responses["alpha2country"].apply(
        lambda x: x.strip().upper() if x else x
    )

    # Add canonical_country column
    df_responses["canonical_country"] = df_responses["alpha2country"].map(
        lambda x: constants.COUNTRIES_DATA[x]["name"]
    )

    # Only keep ages 10-24 for what_young_people_want
    if campaign_code == CampaignCode.what_young_people_want:
        df_responses["age"] = df_responses["age"].apply(filter_ages_10_to_24)
        df_responses = df_responses[df_responses["age"].notna()]

    # Make sure the age value 'prefer not to say' always starts with a capital letter
    df_responses["age"] = df_responses["age"].apply(
        lambda x: x.capitalize() if x and x.lower() == "prefer not to say" else x
    )

    # Set ages
    ages = df_responses["age"].unique().tolist()
    ages = [Age(code=age, name=age) for age in ages if age is not None]
    campaign_crud.set_ages(ages=ages)

    # Age bucket
    # Note: Campaigns 'what_women_want' and 'midwives_voices' already contain 'age' as an age bucket
    if (
        campaign_code == CampaignCode.what_women_want
        or campaign_code == CampaignCode.midwives_voices
    ):
        df_responses["age_bucket"] = df_responses["age"]
        df_responses["age_bucket_default"] = df_responses["age"]
    else:
        # Range for age bucket might differ from campaign to campaign
        df_responses["age_bucket"] = df_responses["age"].apply(
            lambda x: get_age_bucket(age=x, campaign_code=campaign_code)
        )

        # Default age bucket, all campaigns will have the same range for age bucket
        df_responses["age_bucket_default"] = df_responses["age"].apply(
            lambda x: get_age_bucket(age=x)
        )

    # Set age buckets
    age_buckets = df_responses["age_bucket"].unique().tolist()
    age_buckets = [
        AgeBucket(code=age_bucket, name=age_bucket)
        for age_bucket in age_buckets
        if age_bucket is not None
    ]
    campaign_crud.set_age_buckets(age_buckets=age_buckets)

    # Set age buckets default
    age_buckets_default = df_responses["age_bucket_default"].unique().tolist()
    age_buckets_default = [
        AgeBucket(code=age_bucket_default, name=age_bucket_default)
        for age_bucket_default in age_buckets_default
        if age_bucket_default is not None
    ]
    campaign_crud.set_age_buckets_default(age_buckets_default=age_buckets_default)

    # Response years
    if campaign_code == CampaignCode.what_women_want_pakistan:
        response_years = df_responses["response_year"].unique().tolist()
    else:
        response_years = []

    # Set response years
    campaign_crud.set_response_years(response_years=response_years)

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
            # For wwwpakistan, extract the province name from the region
            if campaign_code == CampaignCode.what_women_want_pakistan:
                province = extract_province_from_region(region=region)
                countries[alpha2_code].regions.append(
                    Region(code=region, name=region, province=province)
                )
            else:
                countries[alpha2_code].regions.append(Region(code=region, name=region))

    # Create province column
    if campaign_code == CampaignCode.what_women_want_pakistan:
        df_responses["province"] = df_responses["region"].apply(
            lambda x: extract_province_from_region(x)
        )
    else:
        df_responses["province"] = ""

    # Set countries
    campaign_crud.set_countries(countries=countries)

    # Get responses sample column ids
    column_ids = [col.id for col in campaign_crud.get_responses_sample_columns()]

    # Set genders
    genders = []
    if "gender" in column_ids:
        # Make sure the gender value 'prefer not to say' always starts with a capital letter
        df_responses["gender"] = df_responses["gender"].apply(
            lambda x: x.capitalize() if x and x.lower() == "prefer not to say" else x
        )
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

    # Set tmp db as current db
    databases.set_campaign_db(campaign_code=campaign_code, db=db_tmp)


def load_campaign_ngrams_unfiltered(campaign_code: CampaignCode):
    """Load campaign ngrams unfiltered"""

    campaign_crud = CampaignCRUD(campaign_code=campaign_code)
    campaign_service = CampaignService(campaign_code=campaign_code)

    df = campaign_crud.get_dataframe()

    # Q codes available in a campaign
    campaign_q_codes = campaign_crud.get_q_codes()

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


def load_initial_data():
    """Load initial data"""

    load_campaigns_data()
    load_region_coordinates()
    load_translations_cache()


def load_campaigns_data():
    """Load campaigns data"""

    for campaign_code in CampaignCode:
        # TODO: Temporarily skip campaign 'wee'
        if campaign_code == CampaignCode.womens_economic_empowerment:
            continue
        print(f"INFO:\t  Loading data for campaign {campaign_code.value}...")

        try:
            load_campaign_data(campaign_code=campaign_code)
            load_campaign_ngrams_unfiltered(campaign_code=campaign_code)
            ApiCache().clear_cache()
        except (Exception,):
            logger.exception(
                f"""Error loading data for campaign {campaign_code.value}"""
            )

    print(f"INFO:\t  Loading campaigns data completed.")


def reload_campaigns_data(clear_api_cache: bool, clear_bucket: bool):
    """Reload campaigns data"""

    load_campaigns_data()

    # Clear the API cache
    if clear_api_cache:
        ApiCache().clear_cache()

    # Clear bucket
    if clear_bucket:
        cloud_storage_interactions.clear_bucket()


def load_translations_cache():
    """Load translations cache"""

    print("INFO:\t  Loading translations cache...")

    TranslationsCache().load()

    print("INFO:\t  Loading translations cache completed.")


def load_region_coordinates():
    """Load region coordinates"""

    print(f"INFO:\t  Loading region coordinates...")

    region_coordinates_json = "region_coordinates.json"
    new_coordinates_added = False

    if global_variables.region_coordinates:
        coordinates = global_variables.region_coordinates
    else:
        with open(region_coordinates_json, "r") as file:
            coordinates: dict = json.loads(file.read())

    # Get new region coordinates (if coordinate is not in region_coordinates.json)
    focused_on_country_campaigns_codes = [
        CampaignCode.economic_empowerment_mexico,
        CampaignCode.what_women_want_pakistan,
    ]
    for campaign_code in focused_on_country_campaigns_codes:
        campaign_crud = CampaignCRUD(campaign_code=campaign_code)
        countries = campaign_crud.get_countries_list()

        if len(countries) < 1:
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

    # Save region coordinates (Only in development environment)
    if os.getenv("stage", "").lower() == "dev" and new_coordinates_added:
        with open(region_coordinates_json, "w") as file:
            file.write(json.dumps(coordinates, indent=2))

    global_variables.region_coordinates = coordinates

    print(f"INFO:\t  Loading region coordinates completed.")
