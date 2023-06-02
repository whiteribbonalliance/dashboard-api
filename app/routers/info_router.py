from fastapi import APIRouter, status

from app.core.settings import settings

router = APIRouter(prefix="/info")


@router.get(path="/version", status_code=status.HTTP_200_OK)
def show_version():
    return {"version": settings.VERSION}
