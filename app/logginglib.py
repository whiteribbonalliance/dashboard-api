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

import gzip
import json
import logging
from logging import Handler, Formatter

import requests

from app.core.settings import get_settings

settings = get_settings()

NEWRELIC_API_KEY = settings.NEWRELIC_API_KEY
NEW_RELIC_HEADERS = {
    "Api-Key": NEWRELIC_API_KEY,
    "Content-Encoding": "gzip",
    "Content-Type": "application/gzip",
}
PROJECT_NAME = "dashboard-api"
NEW_RELIC_URL = settings.NEW_RELIC_URL


# ----------------------------------------------------------------------------------------------------------------------------
# Custom loggers
# ----------------------------------------------------------------------------------------------------------------------------


class NewRelicHandler(Handler):
    def emit(self, record):
        log_payload = self.format(record)

        if settings.STAGE == "prod" and NEW_RELIC_URL and NEWRELIC_API_KEY:
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
