from pydantic import BaseModel


class Campaign(BaseModel):
    responses_sample: dict
