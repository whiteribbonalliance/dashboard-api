"""
Schedule tasks
"""

import logging

from fastapi import concurrency
from rocketry import Rocketry
from rocketry.args import Session
from rocketry.conds import cron

from app import helpers
from app.logginglib import init_custom_logger
from app.utils import data_loader
from app.services import cloud_storage_interactions

app = Rocketry(executation="async")

logger = logging.getLogger(__name__)
init_custom_logger(logger)


@app.task("true")
async def do_once_load_initial_data(session=Session()):
    """Load initial data"""

    try:
        await concurrency.run_in_threadpool(data_loader.load_initial_data)
    except (Exception,) as e:
        logger.error(f"Error while trying to load data: {str(e)}")

    # Get task
    task = session["do_once_load_initial_data"]

    # Disable task
    task.disabled = True


@app.task(cron("0 */12 * * *"))
async def do_every_12th_hour_reload_data_and_clear_wra_bucket():
    """
    Load data from BigQuery
    Load coordinates
    Clear cloud storage wra bucket

    Runs at minute 0 past every 12th hour
    """

    # Reload data
    try:
        await concurrency.run_in_threadpool(
            data_loader.reload_campaigns_data, True, True
        )
    except (Exception,) as e:
        logger.error(f"Error while trying to reload data: {str(e)}")

    # Reload region coordinates
    try:
        await concurrency.run_in_threadpool(data_loader.load_region_coordinates)
    except (Exception,) as e:
        logger.error(f"Error while trying to reload region coordinates: {str(e)}")

    # Clear cloud storage wra bucket
    try:
        await concurrency.run_in_threadpool(cloud_storage_interactions.clear_bucket)
    except (Exception,) as e:
        logger.error(f"Error while trying to clear cloud storage wra bucket: {str(e)}")


@app.task(cron("0 * * * *"))
async def do_every_hour_clear_tmp_dir():
    """
    Clear tmp dir

    Runs every hour
    """

    try:
        await concurrency.run_in_threadpool(helpers.clear_tmp_dir)
    except (Exception,) as e:
        logger.error(f"Error while clearing tmp dir: {str(e)}")
