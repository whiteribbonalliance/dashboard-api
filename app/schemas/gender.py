from pydantic import BaseModel, Field


class Gender(BaseModel):
    code: str = Field(description="The gender's code is same as the gender's name")
    name: str = Field(description="The gender")
