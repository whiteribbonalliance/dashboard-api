from pydantic import BaseModel


class Campaign(BaseModel):
    responses_sample: dict[str, list[dict[str, str]]]
    responses_breakdown: list[dict]
