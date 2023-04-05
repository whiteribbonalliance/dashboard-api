from typing import List

from pydantic import BaseModel, Field

from schemas.requests.text import Question


class MatchResponse(BaseModel):
    questions: List[Question] = Field(
        description='The questions which were matched, in an order matching the order of the matrix')
    matches: List[List] = Field(description='Matrix of cosine similarity matches')
