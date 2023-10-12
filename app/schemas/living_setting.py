from pydantic import BaseModel, Field


class LivingSetting(BaseModel):
    code: str = Field(
        description="The living setting's code is same as the living setting's name"
    )
    name: str = Field(description="The living setting")
