"""Fetch campaign data from BigQuery"""

import logging

from google.cloud import bigquery
from google.cloud import bigquery_storage
from google.oauth2 import service_account
from pandas import DataFrame

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


def get_campaign_df_from_bigquery(campaign: str) -> DataFrame:
    """
    Get the dataframe of a campaign from BigQuery

    :param campaign: The campaign
    """

    bigquery_client = get_bigquery_client()

    # Use BigQuery Storage client for faster results to dataframe
    bigquery_storage_client = get_bigquery_storage_client()

    query_job = bigquery_client.query(
        f"""
        SELECT CASE WHEN response_english_text IS null THEN response_original_text ELSE CONCAT(response_original_text, ' (', response_english_text, ')')  END as raw_response,
        respondent_country_code as alpha2country,
        response_nlu_category AS canonical_code,
        response_lemmatized_text as lemmatized,
        respondent_region_name as Region,
        coalesce(cast(respondent_age as string),respondent_age_bucket) as age,
        INITCAP(respondent_gender) as gender,
        JSON_VALUE(respondent_additional_fields.profession) as professional_title,
        FROM deft-stratum-290216.{table_name}
        WHERE campaign = '{campaign}'
        AND response_original_text is not null
        AND (respondent_age > 14 OR respondent_age is null)
        AND respondent_country_code is not null
        AND response_nlu_category is not null
        AND response_lemmatized_text is not null
        AND LENGTH(response_original_text) > 3
       """
    )

    results = query_job.result()

    df_responses = results.to_dataframe(bqstorage_client=bigquery_storage_client)

    return df_responses
