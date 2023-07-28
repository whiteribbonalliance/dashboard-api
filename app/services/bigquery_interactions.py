"""Fetch campaign data from BigQuery"""

import logging

from google.cloud import bigquery
from google.cloud import bigquery_storage
from google.oauth2 import service_account
from pandas import DataFrame

from app.enums.campaign_code import CampaignCode
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


def get_campaign_df_from_bigquery(campaign_code: CampaignCode) -> DataFrame:
    """
    Get the dataframe of a campaign from BigQuery

    :param campaign_code: The campaign code
    """

    bigquery_client = get_bigquery_client()

    # Use BigQuery Storage client for faster results to dataframe
    bigquery_storage_client = get_bigquery_storage_client()

    # PMNCH has a different minimum age
    if campaign_code == CampaignCode.what_young_people_want:
        min_age = "10"
    else:
        min_age = "15"

    query_job = bigquery_client.query(
        f"""
        SELECT CASE WHEN response_english_text IS null THEN response_original_text ELSE CONCAT(response_original_text, ' (', response_english_text, ')')  END as raw_response,
        response_original_lang as original_language,
        respondent_country_code as alpha2country,
        response_nlu_category AS canonical_code,
        response_lemmatized_text as lemmatized,
        respondent_region_name as region,
        coalesce(cast(respondent_age as string),respondent_age_bucket) as age,
        REGEXP_REPLACE(REGEXP_REPLACE(INITCAP(respondent_gender), 'Twospirit', 'Two Spirit'), 'Unspecified', 'Prefer Not To Say') as gender,
        JSON_VALUE(respondent_additional_fields.profession) as profession,
        FROM deft-stratum-290216.{table_name}
        WHERE campaign = '{campaign_code.value}'
        AND response_original_text is not null
        AND (respondent_age >= {min_age} OR respondent_age is null)
        AND respondent_country_code is not null
        AND response_nlu_category is not null
        AND response_lemmatized_text is not null
        AND LENGTH(response_original_text) > 3
       """
    )

    results = query_job.result()

    df_responses = results.to_dataframe(bqstorage_client=bigquery_storage_client)

    return df_responses
