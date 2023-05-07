from typing import List

from fastapi import APIRouter

from schemas.requests.text import CampaignResponse, FilterOptions
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


@router.post(path="/get_responses")
def submit_responses(responses: List[FilterOptions]) -> FilterResponse:
    """
    Retrieve response data for graphs to display in dashboard.

    TODO
    """
    pass