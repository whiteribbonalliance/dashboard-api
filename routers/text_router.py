from typing import List

from fastapi import APIRouter

from schemas.requests.text import CampaignResponse
from schemas.responses.text import SubmitStatus

from fastapi_utils.tasks import repeat_every
from bigquery_interactions import *

import logging
from logginglib import init_custom_logger

logger = logging.getLogger(__name__)
init_custom_logger(logger)

import queue

router = APIRouter(prefix="/text")
BigQueryQueue = queue.Queue()
BQ_FLUSH_INTERVAL: int = 10


@router.on_event("startup")
@repeat_every(seconds=BQ_FLUSH_INTERVAL, logger=logger)
def flush_response_to_bigquery():
    """Flushes all responses from the queue to the bigquery. Fallbacks to local filesystem (via logging) on any BQ error. Unsuccesful records later could be extracted from logs."""
    result_list = []
    while not BigQueryQueue.empty():
        result_list.extend(BigQueryQueue.get())

    if not result_list:
        return

    serializable = [resp.dict() for resp in result_list]

    # a workaround to convert dates into strings
    for resp in serializable:
        if resp["response_date"]:
            resp["response_date"] = resp["response_date"].strftime("%Y-%m-%d")

    if not data_to_bigquery(data_lines=serializable, table_name=BIGQUERY_TABLE_NAME, schema=FULL_RESPONSES_SCHEMA):
        logger.error("Failed submitting %d lines to BigQuery", len(result_list), extra={"records": serializable})
        # put results back onlto the queue?


@router.post(path="/submit_response")
def submit_responses(responses: List[CampaignResponse]) -> SubmitStatus:
    """
    Submit survey responses to a python queue and return immediately (to allow high throughput). Later they will be submitted to BigQuery in batch.
    """
    try:
        BigQueryQueue.put(responses)
        return SubmitStatus(is_success=True)
    except Exception as e:
        logger.error("Error when adding %d responses to the BigQueryQueue: %s", len(responses), e, extra=responses)
        return SubmitStatus(is_success=False)
