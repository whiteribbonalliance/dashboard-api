"""Partially copied from ETL/bigquery_importers.py"""

# ----------------------------------------------------------------------------------------------------------------------------
# LOGGING
# ----------------------------------------------------------------------------------------------------------------------------

import logging

from google.cloud.bigquery import Client
from google.oauth2 import service_account
from pandas import DataFrame

from app.logginglib import init_custom_logger

logger = logging.getLogger(__name__)
init_custom_logger(logger)

table_name = "wra_prod.responses"


def get_bigquery_client() -> Client:
    """Get BigQuery client"""

    credentials = service_account.Credentials.from_service_account_file(
        filename="credentials.json",
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    return Client(
        credentials=credentials,
        project=credentials.project_id,
    )


def get_campaign_df_from_bigquery(campaign: str) -> DataFrame:
    """
    Get the dataframe of a campaign from BigQuery

    :param campaign: The campaign
    """

    client = get_bigquery_client()

    query_job = client.query(
        f"""
        SELECT CASE WHEN response_english_text IS null THEN response_original_text ELSE CONCAT(response_original_text, ' (', response_english_text, ')')  END as raw_response,
        respondent_country_code as alpha2country,
        response_nlu_category AS canonical_code,
        response_lemmatized_text as lemmatized,
        respondent_region_name as Region,
        coalesce(cast(respondent_age as string),respondent_age_bucket) as age,
        INITCAP(respondent_gender) as gender,
        JSON_VALUE(respondent_additional_fields.profession) as professional_title,
        FROM deft-stratum-290216.wra_prod.responses
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
    df_responses = results.to_dataframe()

    return df_responses
