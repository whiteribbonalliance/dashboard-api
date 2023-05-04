"""Partially copied from ETL/bigquery_importers.py"""

# ----------------------------------------------------------------------------------------------------------------------------
# LOGGING
# ----------------------------------------------------------------------------------------------------------------------------

import logging
from logginglib import init_custom_logger

logger = logging.getLogger(__name__)
init_custom_logger(logger)


from google.cloud.bigquery import SchemaField
from google.oauth2 import service_account
from google.cloud import bigquery
from time import sleep
import os

BQ_KEY_PATH = "credentials.json"
credentials = service_account.Credentials.from_service_account_file(
    BQ_KEY_PATH,
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)

bigquery_client = bigquery.Client(
    credentials=credentials,
    project=credentials.project_id,
)

BIGQUERY_TABLE_NAME = "wra_prod.responses"

FULL_RESPONSES_SCHEMA = [
    SchemaField("campaign", "string"),
    SchemaField("mobilizer_name", "string"),
    SchemaField("mobilizer_contact_number", "int64"),
    SchemaField("respondent_additional_fields", "json"),
    SchemaField("respondent_age", "int64"),
    SchemaField("respondent_age_bucket", "string"),
    SchemaField("respondent_contact_number", "int64"),
    SchemaField("respondent_country_code", "string"),
    SchemaField("respondent_gender", "string"),
    SchemaField("respondent_id", "string"),
    SchemaField("respondent_language", "string"),
    SchemaField("respondent_name", "string"),
    SchemaField("respondent_region_code", "string"),
    SchemaField("respondent_region_name", "string"),
    SchemaField("response_consent", "bool"),
    SchemaField("response_date", "date"),
    SchemaField("response_free_text", "string"),
    SchemaField("response_nlu_category", "string"),
    SchemaField("response_nlu_confidence", "float64"),
    SchemaField("response_original_lang", "string"),
    SchemaField("response_original_text", "string"),
    SchemaField("source", "string"),
]


def data_to_bigquery(data_lines: list, schema: list, table_name: str = BIGQUERY_TABLE_NAME, delay: float = 0.1):
    """Submits a list of JSON records into BigQuery"""

    job_config = bigquery.LoadJobConfig(
        schema=schema,
    )

    try:
        job = bigquery_client.load_table_from_json(json_rows=data_lines, destination=table_name, job_config=job_config)
    except Exception as e:
        logger.error("BigQuery saving error: %s, job.errors=%s", e, job.errors)
        return

    while True:
        try:
            state = job.result().state
        except Exception as e:
            logger.error("BigQuery saving error: %s, job.errors=%s", e, job.errors)
            return

        if state in ("DONE", "FAILED"):
            break

        sleep(delay)

    if state == "FAILED" or job.errors:
        logger.error("Errors at loading text data into BigQuery: %s", job.errors)
    else:
        logger.info("Submitted %d line(s) to BigQuery", len(data_lines))
        return True
