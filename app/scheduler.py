"""
Scheduler contains a task that runs every 12th hour to load data from BigQuery
"""

from rocketry import Rocketry
from rocketry.conds import cron

from app.utils import data_loader

app = Rocketry()


@app.task(cron("0 */12 * * *"))
def do_every_12th_hour():
    """
    Load data from BigQuery
    Runs at minute 0 past every 12th hour
    """

    data_loader.load_data()
