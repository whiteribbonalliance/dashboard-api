from fastapi import APIRouter, status

from app.core.settings import settings
from app.enums.api_prefix import ApiPrefix

router = APIRouter(prefix=f"/{ApiPrefix.v1}/info")


@router.get(path="/version", status_code=status.HTTP_200_OK)
def show_version():
    return {"version": settings.VERSION}
