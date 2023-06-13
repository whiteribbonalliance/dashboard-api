from pydantic import BaseModel, Field


class Region(BaseModel):
    code: str = Field(description="The region's code is same as the region's name")
    name: str = Field(description="The region's name")
