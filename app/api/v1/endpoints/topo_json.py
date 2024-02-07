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

import json
import logging

from fastapi import APIRouter, status

from app.http_exceptions import ResourceNotFoundHTTPException
from app.logginglib import init_custom_logger

logger = logging.getLogger(__name__)
init_custom_logger(logger)

router = APIRouter(prefix="/topo-json")


@router.get(
    path="/{alpha2_code}",
    status_code=status.HTTP_200_OK,
)
def read_topo_json(alpha2_code: str):
    """Read TopoJSON"""

    if alpha2_code.lower() == "mx":
        # Source credit: https://gist.githubusercontent.com/diegovalle/5129746/raw/c1c35e439b1d5e688bca20b79f0e53a1fc12bf9e/mx_tj.json
        with open("topo_json_mx.json", "r", encoding="utf-8") as file:
            return json.loads(file.read())

    raise ResourceNotFoundHTTPException("No TopoJSON found for country.")
