from pydantic import BaseModel, Field


class ResponseColumn(BaseModel):
    name: str = Field(description="The name")
    id: str = Field(description="The id")
    type: str = Field(description="The type")
