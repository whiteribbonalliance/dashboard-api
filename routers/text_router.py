from typing import List

from fastapi import APIRouter

from schemas.requests.text import RawFile, Instrument
from util.parsing.files_to_instruments import convert_files_to_instruments

router = APIRouter(prefix="/text")


@router.post(
    path="/parse"
)
def parse_instruments(files: List[RawFile]) -> List[Instrument]:
    """
    Parse PDFs or Excels or text files into Instruments, and identifies the language.

    If the file is binary (Excel or PDF), you must supply each file with the content in MIME format and the bytes in base64 encoding, like the example RawFile in the schema.

    If the file is plain text, supply the file content as a standard string.

    """

    return convert_files_to_instruments(files)

@router.post(
    path="/match"
)
def match(instruments: List[Instrument]) -> list:
    """
    Match instruments

    """
    pass
