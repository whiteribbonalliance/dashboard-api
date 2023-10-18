from pydantic import BaseModel, Field


class OptionBool(BaseModel):
    value: bool = Field(default="The value")
    label: str = Field(description="The label")
    metadata: str = Field(default="", description="The metadata")
