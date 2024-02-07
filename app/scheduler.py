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

import logging

from fastapi import concurrency
from rocketry import Rocketry
from rocketry.args import Session
from rocketry.conds import cron

from app import utils
from app.core.settings import get_settings
from app.helpers import data_loader
from app.logginglib import init_custom_logger

settings = get_settings()

app = Rocketry(executation="async")

logger = logging.getLogger(__name__)
init_custom_logger(logger)


@app.task("true")
async def do_once_load_initial_data(session=Session()):
    """
    Load initial data.
    """

    await concurrency.run_in_threadpool(data_loader.load_initial_data)

    # Get task
    task = session["do_once_load_initial_data"]

    # Disable task
    task.disabled = True


@app.task(cron("0 */12 * * *"))
async def do_every_12th_hour_reload_data():
    """
    Reload data.
    Runs at minute 0 past every 12th hour.
    """

    await concurrency.run_in_threadpool(data_loader.reload_data, True, True, True)


@app.task(cron("0 * * * *"))
async def do_every_hour_clear_tmp_dir(session=Session()):
    """
    Clear tmp dir.
    Runs every hour.
    """

    # The tmp dir is only used when deployment is done at Google App Engine
    if settings.CLOUD_SERVICE != "google":
        # Get task
        task = session["do_every_hour_clear_tmp_dir"]

        # Disable task
        task.disabled = True

        return

    await concurrency.run_in_threadpool(utils.clear_tmp_dir)
