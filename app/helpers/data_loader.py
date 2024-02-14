"""
MIT License

Copyright (c) 2023 World We Want. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

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

import copy
import json
import logging
import math
from io import StringIO

import pandas as pd
import requests

from app import constants, databases, utils
from app import crud
from app import global_variables
from app.core.settings import get_settings
from app.enums.legacy_campaign_code import LegacyCampaignCode
from app.helpers import q_codes_finder, q_col_names
from app.helpers.campaigns_config_loader import CAMPAIGNS_CONFIG
from app.logginglib import init_custom_logger
from app.schemas.country import Country
from app.schemas.region import Region
from app.services import azure_blob_storage_interactions
from app.services import google_cloud_storage_interactions
from app.services import google_maps_interactions
from app.services.api_cache import ApiCache
from app.services.campaign import CampaignService
from app.services.translations_cache import TranslationsCache

logger = logging.getLogger(__name__)
init_custom_logger(logger)

settings = get_settings()


def load_campaign_data(campaign_code: str):
    """
    Load campaign data.

    :param campaign_code: The campaign code.
    """

    # Will create a tmp copy of the db to write campaign data to
    # If writing of the data succeeds, then the current db will be replaced with the tmp db at the end of this function
    # This is to make sure new data loads correctly into the db
    # If an error occurs while loading new data, then the current db stays as is and the error is logged
    db_tmp = copy.deepcopy(databases.get_campaign_db(campaign_code=campaign_code))

    # CRUD
    campaign_crud = crud.Campaign(campaign_code=campaign_code, db=db_tmp)

    # Get df
    df_responses = load_campaign_df(campaign_code=campaign_code)
    if df_responses is None:
        raise Exception(f"Could not load dataframe for campaign {campaign_code}.")

    # Q codes
    campaign_q_codes = q_codes_finder.find_in_df(df=df_responses)

    # Set q codes
    campaign_crud.set_q_codes(q_codes=campaign_q_codes)

    def parse_df():
        # Check if all required columns are present
        required_columns = utils.get_required_columns(q_codes=campaign_q_codes)
        for required_column in required_columns:
            if required_column not in df_responses.columns.tolist():
                if required_column.endswith("_lemmatized"):
                    raise Exception(
                        f"""Required column {required_column} not found in campaign {campaign_code}. \nPlease run: python lemmatize_responses.py {campaign_code}"""
                    )
                else:
                    raise Exception(
                        f"Required column {required_column} not found in campaign {campaign_code}."
                    )

        # Make sure these optional columns are created with empty values if they are not present
        columns_to_check_if_present = [
            "region",
            "province",
            "gender",
            "ingestion_time",
            "data_source",
            "profession",
            "setting",
            "response_year",
        ]
        for column_to_check_if_present in columns_to_check_if_present:
            if column_to_check_if_present not in df_responses.columns.tolist():
                df_responses[column_to_check_if_present] = ""

        def calculate_age_midpoint_range(age: str) -> str:
            age_replaced = age.replace("+", "")
            if age_replaced.isnumeric():
                return age_replaced

            age_split = age.split("-")
            if len(age_split) == 2:
                age_1 = age_split[0]
                age_2 = age_split[1]
                if age_1.isnumeric() and age_2.isnumeric():
                    age_midpoint_range = math.floor((int(age_1) + int(age_2)) / 2)

                    return str(age_midpoint_range)

            return age

        def strip_value(x: str):
            return x.strip() if x else x

        def title_value(x: str):
            return x.title() if x else x

        def capitalize_value(x: str):
            return x.capitalize() if x else x

        def strip_and_upper_value(x: str):
            return x.strip().upper() if x else x

        def title_prefer_not_to_say(x: str):
            return x.title() if x and x.lower() == "prefer not to say" else x

        # Value 'prefer not to say' should always start with a capital letter
        df_responses["setting"] = df_responses["setting"].apply(title_prefer_not_to_say)
        df_responses["gender"] = df_responses["gender"].apply(title_prefer_not_to_say)
        df_responses["age"] = df_responses["age"].apply(title_prefer_not_to_say)

        # Apply title
        df_responses["setting"] = df_responses["setting"].apply(title_value)
        df_responses["profession"] = df_responses["profession"].apply(title_value)

        # Apply strip and upper
        df_responses["alpha2country"] = df_responses["alpha2country"].apply(
            strip_and_upper_value
        )

        # Apply strip
        df_responses["setting"] = df_responses["setting"].apply(strip_value)
        df_responses["profession"] = df_responses["profession"].apply(strip_value)
        df_responses["region"] = df_responses["region"].apply(strip_value)
        df_responses["province"] = df_responses["province"].apply(strip_value)
        df_responses["age"] = df_responses["age"].apply(strip_value)
        df_responses["gender"] = df_responses["gender"].apply(strip_value)
        df_responses["response_year"] = df_responses["response_year"].apply(strip_value)

        # Capitalize responses
        for q_code in campaign_q_codes:
            df_responses[
                q_col_names.get_response_col_name(q_code=q_code)
            ] = df_responses[q_col_names.get_response_col_name(q_code=q_code)].apply(
                capitalize_value
            )

        # Add canonical_country column
        df_responses["canonical_country"] = df_responses["alpha2country"].map(
            lambda x: constants.COUNTRIES_DATA[x]["name"]
        )

        # Age bucket
        # Note: Legacy campaigns wra03a and midwife contain age as an age bucket
        # The data from age will be moved to age_bucket and then age will be set to an empty string
        if (
            campaign_code == LegacyCampaignCode.wra03a.value
            or campaign_code == LegacyCampaignCode.midwife.value
        ):
            df_responses["age_bucket"] = df_responses["age"]
            df_responses["age_bucket_default"] = df_responses["age"]
            df_responses["age"] = ""
        else:
            # Range for age bucket might differ from campaign to campaign
            df_responses["age_bucket"] = df_responses["age"].apply(
                lambda x: get_age_bucket(age=x, campaign_code=campaign_code)
            )

            # Default age bucket, all campaigns will have the same range
            df_responses["age_bucket_default"] = df_responses["age"].apply(
                lambda x: get_age_bucket(age=x)
            )

        # Age midpoint range
        if (
            campaign_code == LegacyCampaignCode.wra03a.value
            or campaign_code == LegacyCampaignCode.midwife.value
        ):
            df_responses["age_midpoint_range"] = df_responses["age"].apply(
                calculate_age_midpoint_range
            )
        else:
            df_responses["age_midpoint_range"] = df_responses["age"]

    def load_db():
        # Set ages
        ages = df_responses["age"].unique().tolist()
        ages = [age for age in ages if age]
        campaign_crud.set_ages(ages=ages)

        # Set age buckets
        if (
            campaign_code == LegacyCampaignCode.allcampaigns.value
            or campaign_code == LegacyCampaignCode.dataexchange.value
        ):
            # For these campaigns use age_bucket_default as age_bucket
            # These campaigns contain data from all other campaigns merged together and each campaign might have different age_bucket
            # age_bucket_default is same across all campaigns
            df_responses["age_bucket"] = df_responses["age_bucket_default"]
        age_buckets = df_responses["age_bucket"].unique().tolist()
        age_buckets = [x for x in age_buckets if x]
        campaign_crud.set_age_buckets(age_buckets=age_buckets)

        # Set age buckets default
        age_buckets_default = df_responses["age_bucket_default"].unique().tolist()
        age_buckets_default = [x for x in age_buckets_default if x]
        campaign_crud.set_age_buckets_default(age_buckets_default=age_buckets_default)

        # Set response years
        response_years = df_responses["response_year"].unique().tolist()
        response_years = [x for x in response_years if x]
        campaign_crud.set_response_years(response_years=response_years)

        # Create countries
        countries: dict[str, Country] = {}
        countries_alpha2_codes = df_responses[["alpha2country"]].drop_duplicates()
        for idx in range(len(countries_alpha2_codes)):
            alpha2_code = countries_alpha2_codes["alpha2country"].iloc[idx]
            country = constants.COUNTRIES_DATA.get(alpha2_code)
            countries[alpha2_code] = Country(
                alpha2_code=alpha2_code,
                name=country.get("name"),
                demonym=country.get("demonym"),
            )

        # Add regions and provinces to countries
        unique_canonical_country_region_province = df_responses[
            ["alpha2country", "region", "province"]
        ].drop_duplicates()
        for idx in range(len(unique_canonical_country_region_province)):
            alpha2_code = unique_canonical_country_region_province[
                "alpha2country"
            ].iloc[idx]
            region = unique_canonical_country_region_province["region"].iloc[idx]
            province = unique_canonical_country_region_province["province"].iloc[idx]
            if region:
                country = countries.get(alpha2_code)
                if country and (region not in country.regions):
                    country.regions.append(
                        Region(code=region, name=region, province=province)
                    )

        # Set countries
        campaign_crud.set_countries(countries=countries)

        # Set genders
        genders = []
        for gender in df_responses["gender"].value_counts().index:
            if gender:
                genders.append(gender)
        campaign_crud.set_genders(genders=genders)

        # Set living settings
        living_settings = []
        for living_setting in df_responses["setting"].value_counts().index:
            if living_setting:
                living_settings.append(living_setting)
        campaign_crud.set_living_settings(living_settings=living_settings)

        # Set professions
        professions = []
        for profession in df_responses["profession"].value_counts().index:
            professions.append(profession)
        campaign_crud.set_professions(professions=professions)

        # Set dataframe
        campaign_crud.set_dataframe(df=df_responses)

        # Set tmp db as current db
        databases.set_campaign_db(campaign_code=campaign_code, db=db_tmp)

    # These campaigns use data from other campaigns whose df was already parsed
    if (
        campaign_code != LegacyCampaignCode.allcampaigns.value
        and campaign_code != LegacyCampaignCode.dataexchange.value
    ):
        parse_df()

    load_db()


def load_campaign_df(campaign_code: str) -> pd.DataFrame | None:
    """
    Load campaign dataframe.

    Will first check if a local file was provided, then if URL was provided, then from the cloud.
    """

    df: pd.DataFrame | None = None
    dtype = {"age": str, "response_year": str}

    # Load data for campaign
    if campaign_config := CAMPAIGNS_CONFIG.get(campaign_code):
        keep_default_na = False

        # From local file
        if campaign_config.file.local:
            df = pd.read_csv(
                filepath_or_buffer=campaign_config.filepath,
                keep_default_na=keep_default_na,
                dtype=dtype,
            )

        # From URL
        elif campaign_config.file.url:
            response = requests.get(url=campaign_config.file.url)
            if response.ok:
                df = pd.read_csv(
                    filepath_or_buffer=StringIO(response.content.decode("utf-8")),
                    keep_default_na=keep_default_na,
                    dtype=dtype,
                )

        # From cloud
        elif campaign_config.file.cloud:
            if settings.CLOUD_SERVICE == "google":
                blob = google_cloud_storage_interactions.get_blob(
                    bucket_name=settings.GOOGLE_CLOUD_STORAGE_BUCKET_FILE,
                    blob_name=campaign_config.file.cloud,
                )
                df = pd.read_csv(
                    filepath_or_buffer=StringIO(
                        blob.download_as_bytes().decode("utf-8")
                    ),
                    keep_default_na=False,
                    dtype=dtype,
                )
            elif settings.CLOUD_SERVICE == "azure":
                blob = azure_blob_storage_interactions.get_blob(
                    container_name=settings.AZURE_STORAGE_CONTAINER_FILE,
                    blob_name=campaign_config.file.cloud,
                )
                df = pd.read_csv(
                    filepath_or_buffer=StringIO(blob.readall().decode("utf-8")),
                    keep_default_na=False,
                    dtype=dtype,
                )

        # From other campaigns
        elif campaign_config.file.use_campaigns:
            df_list: list[pd.DataFrame] = []
            for other_campaign_config in CAMPAIGNS_CONFIG.values():
                # Skip on these conditions
                if other_campaign_config.file.use_campaigns:
                    continue
                if (
                    other_campaign_config.campaign_code
                    not in campaign_config.file.use_campaigns
                ):
                    continue

                # Get campaign db
                db_campaign = databases.get_campaign_db(
                    campaign_code=other_campaign_config.campaign_code
                )

                # Add campaign df to df_list
                if db_campaign:
                    df_list.append(db_campaign.dataframe)

            if df_list:
                df = pd.concat(df_list)

    if df is not None:
        # ingestion_time to datetime
        if "ingestion_time" in df.columns.tolist():
            df["ingestion_time"] = pd.to_datetime(df["ingestion_time"])

        df = df.fillna("")

        return df
    else:
        raise Exception(f"Could not load dataframe for campaign {campaign_code}.")


def get_age_bucket(age: str | int | None, campaign_code: str = None) -> str | None:
    """Convert age to an age bucket e.g. '30' to '25-34'"""

    if age is None:
        return age

    if isinstance(age, str):
        if age.isnumeric():
            age = int(age)
        else:
            return age  # Non-numeric e.g. 'Prefer not to say' or age value is already an age bucket

    if campaign_code == LegacyCampaignCode.healthwellbeing.value:
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
        if age >= 10:
            return "10-14"
        if age >= 0:
            return "< 10"

    return "N/A"


def load_campaign_ngrams_unfiltered(campaign_code: str):
    """Load campaign ngrams unfiltered"""

    campaign_crud = crud.Campaign(campaign_code=campaign_code)
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

    global_variables.is_loading_data = True

    try:
        # Load data
        load_translations_cache()
        load_campaigns_data()
        load_region_coordinates()
    except (Exception,) as e:
        logger.error(f"An error occurred while loading initial data: {str(e)}")

    global_variables.is_loading_data = False
    global_variables.initial_loading_data_complete = True


def reload_data(
    clear_api_cache: bool,
    clear_google_cloud_storage_bucket: bool,
    clear_azure_blob_storage_container,
):
    """Reload data"""

    if global_variables.is_loading_data:
        return

    global_variables.is_loading_data = True

    try:
        # Reload data
        load_campaigns_data()
        load_region_coordinates()

        # Clear the API cache
        if clear_api_cache:
            ApiCache().clear_cache()

        # A list of blobs to skip from deleting (Only the unfiltered dataset should stay cached).
        # The filename/blob_name of an unfiltered dataset can look like export_healthwellbeing.csv (Will not be deleted).
        # The filename/blob_name of a filtered dataset can look like export_healthwellbeing_a53aaf6fe.csv (Will be deleted).
        skip_blobs = [
            f"export_{x.campaign_code}.csv" for x in CAMPAIGNS_CONFIG.values()
        ]

        # Clear bucket
        if clear_google_cloud_storage_bucket and settings.CLOUD_SERVICE == "google":
            google_cloud_storage_interactions.clear_bucket(
                bucket_name=settings.GOOGLE_CLOUD_STORAGE_BUCKET_TMP_DATA,
                skip_blobs=skip_blobs,
            )

        # Clear container as the data cached might be out of date
        elif clear_azure_blob_storage_container and settings.CLOUD_SERVICE == "azure":
            azure_blob_storage_interactions.clear_container(
                container_name=settings.AZURE_STORAGE_CONTAINER_TMP_DATA,
                skip_blobs=skip_blobs,
            )
    except (Exception,) as e:
        logger.error(f"An error occurred while reloading data: {str(e)}")

    global_variables.is_loading_data = False


def load_campaigns_data():
    """Load campaigns data"""

    # Campaigns that depend on data from other campaigns should be added at last
    campaigns_configs = [
        x for x in CAMPAIGNS_CONFIG.values() if not x.file.use_campaigns
    ]
    campaigns_configs.extend(
        [x for x in CAMPAIGNS_CONFIG.values() if x.file.use_campaigns]
    )
    for campaign_config in campaigns_configs:
        print(f"INFO:\t  Loading data for campaign {campaign_config.campaign_code}...")

        # Will temporarily use db from dataexchange instead
        if campaign_config.campaign_code == LegacyCampaignCode.allcampaigns.value:
            continue

        try:
            load_campaign_data(campaign_code=campaign_config.campaign_code)
            load_campaign_ngrams_unfiltered(campaign_code=campaign_config.campaign_code)
            ApiCache().clear_cache()
        except (Exception,):
            logger.exception(
                f"""Error loading data for campaign {campaign_config.campaign_code}"""
            )

    print(f"INFO:\t  Loading campaigns data completed.")


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
    focused_on_country_campaigns_codes = []
    for campaign_code in [x.campaign_code for x in CAMPAIGNS_CONFIG.values()]:
        if (
            campaign_code == LegacyCampaignCode.giz.value
            or campaign_code == LegacyCampaignCode.wwwpakistan.value
        ):
            focused_on_country_campaigns_codes.append(campaign_code)

    for campaign_code in focused_on_country_campaigns_codes:
        campaign_crud = crud.Campaign(campaign_code=campaign_code)
        countries = campaign_crud.get_countries_list()

        if not countries:
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
            coordinate = google_maps_interactions.get_coordinate(
                location=f"{location_country_name}, {location_name}"
            )

            # Add coordinate to coordinates
            if not coordinates.get(location_country_alpha2_code):
                coordinates[location_country_alpha2_code] = {}
            coordinates[location_country_alpha2_code][location_name] = coordinate

            if not new_coordinates_added:
                new_coordinates_added = True

    # Save region coordinates (Only in dev)
    if settings.STAGE == "dev" and new_coordinates_added:
        with open(region_coordinates_json, "w") as file:
            file.write(json.dumps(coordinates, indent=2))

    global_variables.region_coordinates = coordinates

    print(f"INFO:\t  Loading region coordinates completed.")
