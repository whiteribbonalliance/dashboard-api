from typing import List

from fastapi import APIRouter

from schemas.requests.text import CampaignResponse
from schemas.responses.text import SubmitStatus

router = APIRouter(prefix="/text")


@router.post(
    path="/submit_response"
)
def submit_response(files: List[CampaignResponse]) -> SubmitStatus:
    """
    Submit survey response
    """

    return SubmitStatus(is_success=True)
