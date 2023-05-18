from pydantic import BaseModel, Field


class FilterOptions(BaseModel):
    campaign: str = Field(
        description="Unique identifier for the campaign",
    )

    respondent_country_code: str = Field(
        None, description="The alpha-2 country code of the respondent"
    )
