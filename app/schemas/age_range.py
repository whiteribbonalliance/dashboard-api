from pydantic import BaseModel, Field


class AgeRange(BaseModel):
    code: str = Field(
        description="The age range's code is same as the age range's name"
    )
    name: str = Field(description="The age range's name")
