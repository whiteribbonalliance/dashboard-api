from pydantic import BaseModel, Field


class Campaign(BaseModel):
    data: str = Field(description="Test data")
