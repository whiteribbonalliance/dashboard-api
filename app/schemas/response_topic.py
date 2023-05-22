from pydantic import BaseModel, Field


class ResponseTopic(BaseModel):
    code: str = Field(description="The response topic's code")
    name: str = Field(description="The response topic's name")
