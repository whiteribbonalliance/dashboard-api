"""Fetch campaign data from BigQuery"""

import logging

from google.cloud import bigquery
from google.cloud import bigquery_storage
from google.oauth2 import service_account
from pandas import DataFrame

from app.enums.campaign_code import CampaignCode
from app.enums.question_code import QuestionCode
from app.logginglib import init_custom_logger
from app.utils import helpers
from app.utils import q_col_names

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

    import pandas as pd
    df_responses = pd.read_pickle(f"../../{campaign_code.value}.pkl")

    # Get question codes for campaign, e.g. if campaign has question 1 and question 2 -> ["q1", "q2"]
    campaign_q_codes = helpers.get_campaign_q_codes(campaign_code=campaign_code)

    # Add additional columns per question
    for q_code in campaign_q_codes:
        # Q1 columns already exists
        if q_code == QuestionCode.q1:
            continue

        df_responses[q_col_names.get_raw_response_col_name(q_code=q_code)] = ""
        df_responses[q_col_names.get_lemmatized_col_name(q_code=q_code)] = ""
        df_responses[q_col_names.get_canonical_code_col_name(q_code=q_code)] = ""
        df_responses[q_col_names.get_original_language_col_name(q_code=q_code)] = ""

    return df_responses
