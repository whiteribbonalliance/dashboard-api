from pydantic import BaseModel, Field


class Country(BaseModel):
    alpha2_code: str = Field(description="The Country's alpha2 code")
    name: str = Field(description="The country's name")
    demonym: str = Field(description="The country's demonym")
    regions: list[str] = Field(default=[], description="The country's region")
