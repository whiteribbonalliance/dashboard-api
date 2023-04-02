from fastapi import APIRouter

router = APIRouter(prefix="/text")


@router.post(
    path="/parse"
)
def parse_instruments(files: list) -> list:
    """
    Parse PDFs or Excels
    @param body:
    @return:
    """
    pass


@router.post(
    path="/match"
)
def match(instruments: list) -> list:
    """
    Match instruments
    @param body:
    @return:
    """
    pass
