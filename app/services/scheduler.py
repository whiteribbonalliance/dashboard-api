"""
Scheduler contains a task that runs every 12th hour to load data from BigQuery
"""

from fastapi.concurrency import run_in_threadpool
from rocketry import Rocketry
from rocketry.conds import cron

from app.utils import data_loader

app = Rocketry(executation="async")


@app.task(cron("0 */12 * * *"))
async def do_every_12th_hour():
    """
    Load data from BigQuery
    Runs at minute 0 past every 12th hour
    """

    await run_in_threadpool(data_loader.load_data)
