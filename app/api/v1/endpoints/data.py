"""
MIT License

Copyright (c) 2023 White Ribbon Alliance. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

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

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app import global_variables
from app.api import dependencies
from app.logginglib import init_custom_logger
from app.schemas.data_is_loading import DataIsLoading
from app.utils import data_loader

logger = logging.getLogger(__name__)
init_custom_logger(logger)

router = APIRouter(prefix="/data")


@router.get(
    path="/loading-status",
    response_model=DataIsLoading,
    status_code=status.HTTP_200_OK,
)
def read_data_loading_status(_username: str = Depends(dependencies.user_exists_check)):
    """Check if data is loading"""

    return DataIsLoading(is_loading=global_variables.is_loading_data)


@router.post(
    path="/reload",
    status_code=status.HTTP_202_ACCEPTED,
)
def init_data_reloading(
    background_tasks: BackgroundTasks,
    _username: str = Depends(dependencies.user_is_admin_check),
):
    """Init data reloading"""

    if not global_variables.is_loading_data:
        try:
            background_tasks.add_task(data_loader.reload_data, True, True, True)
        except (Exception,) as e:
            logger.error(f"An error occurred while reloading data: {str(e)}")
