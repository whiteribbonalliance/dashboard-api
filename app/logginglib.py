"""This module handles advanced logging. Logging both to a stdout and a centralized 3-rd party DB are supported."""

import os
import gzip
import json
import requests
import logging
from logging import Handler, Formatter
from app import env

# ----------------------------------------------------------------------------------------------------------------------------
# Inits
# ----------------------------------------------------------------------------------------------------------------------------

NEW_RELIC_HEADERS = {
    "Api-Key": os.environ.get("NEWRELIC_API_KEY"),
    "Content-Encoding": "gzip",
    "Content-Type": "application/gzip",
}

PROJECT_NAME = "wra-global-dashboard-api"
NEW_RELIC_URL = "https://log-api.eu.newrelic.com/log/v1"


# ----------------------------------------------------------------------------------------------------------------------------
# Custom loggers
# ----------------------------------------------------------------------------------------------------------------------------


class NewRelicHandler(Handler):
    def emit(self, record):
        log_payload = self.format(record)

        if env.STAGE == "prod":
            requests.post(NEW_RELIC_URL, data=log_payload, headers=NEW_RELIC_HEADERS)


class NewRelicFormatter(Formatter):
    def __init__(self):
        super().__init__()

    def format(self, record):
        message = record.getMessage()
        attributes = {
            key: value
            for key, value in record.__dict__.items()
            if key not in ("args", "message", "msg")
        }
        attributes["projectName"] = PROJECT_NAME
        payload = {
            "message": message,
            "attributes": attributes,
        }
        payload = gzip.compress(json.dumps(payload, default=str).encode("utf-8"))

        return payload


# ----------------------------------------------------------------------------------------------------------------------------
# Global operations on loggers
# ----------------------------------------------------------------------------------------------------------------------------


def init_custom_logger(logger, level: int = logging.INFO):
    # newrelic for centralized logging
    handler = NewRelicHandler()
    formatter = NewRelicFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # streaming for default container logging
    logger.addHandler(logging.StreamHandler())

    logger.setLevel(level)
