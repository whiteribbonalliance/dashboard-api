from pydantic import BaseModel, Field


class OptionStr(BaseModel):
    value: str = Field(default="The value")
    label: str = Field(description="The label")
    metadata: str = Field(default="", description="The metadata")
