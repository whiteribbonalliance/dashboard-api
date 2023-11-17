import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.api import dependencies
from app.logginglib import init_custom_logger
from app.schemas.data_is_loading import DataIsLoading
from app.schemas.parameters_admin import ParametersAdmin
from app.utils import data_loader
from app import global_variables

logger = logging.getLogger(__name__)
init_custom_logger(logger)

router = APIRouter(prefix="/admin")


@router.get(
    path="/data/loading-status",
    response_model=DataIsLoading,
    status_code=status.HTTP_200_OK,
)
def read_data_loading_status(
    _: Annotated[ParametersAdmin, Depends(dependencies.dep_parameters_admin)]
):
    """Check if data is loading"""

    return DataIsLoading(is_loading=global_variables.is_loading_data)


@router.post(
    path="/data/reload",
    status_code=status.HTTP_202_ACCEPTED,
)
def data_reload(
    _: Annotated[ParametersAdmin, Depends(dependencies.dep_parameters_admin)],
    background_tasks: BackgroundTasks,
):
    """Data reload"""

    if not global_variables.is_loading_data:
        try:
            background_tasks.add_task(data_loader.reload_data, True, True)
        except (Exception,) as e:
            logger.error(f"An error occurred while reloading data: {str(e)}")
