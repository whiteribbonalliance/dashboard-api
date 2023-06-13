from pydantic import BaseModel, Field


class Age(BaseModel):
    code: str = Field(description="The age's code is same as the age's name")
    name: str = Field(description="The age's name")
