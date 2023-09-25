from pydantic import BaseModel, Field


class AgeBucket(BaseModel):
    code: str = Field(
        description="The age bucket's code is same as the age bucket's name"
    )
    name: str = Field(description="The age bucket's name")
