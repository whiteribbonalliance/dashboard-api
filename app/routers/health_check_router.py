from fastapi import APIRouter, status

from app.enums.api_prefix import ApiPrefix

router = APIRouter(prefix=f"/{ApiPrefix.v1}/health-check")


@router.get(path="", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok"}
