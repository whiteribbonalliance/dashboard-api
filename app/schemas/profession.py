from pydantic import BaseModel, Field


class Profession(BaseModel):
    code: str = Field(
        description="The profession's code is same as the profession's name"
    )
    name: str = Field(description="The profession's name")
