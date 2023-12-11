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

import logging

import pandas as pd
from google.cloud import bigquery
from google.cloud import bigquery_storage
from google.oauth2 import service_account
from pandas import DataFrame

from app import env
from app.logginglib import init_custom_logger

logger = logging.getLogger(__name__)
init_custom_logger(logger)

table_name = "wra_prod.responses"


def get_bigquery_client() -> bigquery.Client:
    """Get BigQuery client"""

    credentials = service_account.Credentials.from_service_account_file(
        filename="credentials.json",
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    return bigquery.Client(
        credentials=credentials,
        project=credentials.project_id,
    )


def get_bigquery_storage_client() -> bigquery_storage.BigQueryReadClient:
    """Get BigQuery storage client"""

    credentials = service_account.Credentials.from_service_account_file(
        filename="credentials.json",
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    return bigquery_storage.BigQueryReadClient(credentials=credentials)


def get_query(campaign_code: str):
    """Get query"""

    # Set minimum age
    if campaign_code == "pmn01a":
        min_age = "10"
    elif campaign_code == "healthwellbeing":
        min_age = "0"
    else:
        min_age = "15"

    return f"""
        SELECT CASE WHEN response_english_text IS null THEN response_original_text ELSE CONCAT(response_original_text, ' (', response_english_text, ')')  END as q1_raw_response,
        response_original_lang as q1_original_language,
        response_nlu_category AS q1_canonical_code,
        response_lemmatized_text as q1_lemmatized,
        respondent_country_code as alpha2country,
        respondent_region_name as region,
        coalesce(cast(respondent_age as string),respondent_age_bucket) as age,
        REGEXP_REPLACE(REGEXP_REPLACE(INITCAP(respondent_gender), 'Twospirit', 'Two Spirit'), 'Unspecified', 'Prefer Not To Say') as gender,
        ingestion_time as ingestion_time,
        JSON_VALUE(respondent_additional_fields.data_source) as data_source,
        JSON_VALUE(respondent_additional_fields.profession) as profession,
        JSON_VALUE(respondent_additional_fields.setting) as setting,
        JSON_QUERY(respondent_additional_fields, '$.year') as response_year,
        respondent_additional_fields as additional_fields,
        FROM deft-stratum-290216.{table_name}
        WHERE campaign = '{campaign_code}'
        AND response_original_text is not null
        AND (respondent_age >= {min_age} OR respondent_age is null)
        AND respondent_country_code is not null
        AND response_nlu_category is not null
        AND response_lemmatized_text is not null
        AND LENGTH(response_original_text) > 3
       """


def get_campaign_df(campaign_code: str) -> DataFrame:
    """
    Get the dataframe of a campaign from BigQuery

    :param campaign_code: The campaign code
    """

    # Load from .pkl file
    if env.LOAD_FROM_LOCAL_PKL_FILE:
        df_responses = pd.read_pickle(f"{campaign_code}.pkl")

        return df_responses

    # BQ client
    bigquery_client = get_bigquery_client()

    # Use BigQuery Storage client for faster results to dataframe
    bigquery_storage_client = get_bigquery_storage_client()

    # Query
    query = get_query(campaign_code=campaign_code)

    # Query job
    query_job = bigquery_client.query(query)

    # Results
    results = query_job.result()

    # Dataframe
    df_responses = results.to_dataframe(bqstorage_client=bigquery_storage_client)

    # Save to .pkl file
    if env.SAVE_TO_PKL_FILE:
        df_responses.to_pickle(f"{campaign_code}.pkl")

    return df_responses


def export_pmn01a_data_to_pkl():
    """Export data from campaign pmn01a to a Pickle file"""

    # Client
    bigquery_client = get_bigquery_client()

    # Use BigQuery Storage client for faster results to dataframe
    bigquery_storage_client = get_bigquery_storage_client()

    # Query
    query = get_query(campaign_code="pmn01a")

    # Query job
    query_job = bigquery_client.query(query)

    # Results
    results = query_job.result()

    # Dataframe
    df_responses = results.to_dataframe(bqstorage_client=bigquery_storage_client)

    # Save to CSV
    df_responses.to_pickle("pmn01a.pkl")
