from pydantic import BaseModel, Field


class Url(BaseModel):
    url: str = Field(description="Url")
