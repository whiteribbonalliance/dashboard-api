from pydantic import BaseModel


class Campaign(BaseModel):
    responses_sample: dict
    responses_breakdown: list[dict]
    top_words_and_phrases: dict
