from typing import List, Dict

from pydantic import BaseModel, Field

from schemas.enums.file_types import FileType
from schemas.enums.languages import Language


class CampaignResponse(BaseModel):
    campaign_id: str = Field(description="Unique identifier for the campaign")
    response_id: str = Field(None, description="Unique identifier for the response (UUID-4)")
    respondent_name: str = Field(description="The name of the respondent")
    respondent_age: str = Field(description="The age of the respondent (either a value, a range, or N/A)")
    respondent_country_code: str = Field(description="The alpha-2 country code of the respondent")
    respondent_region_code: str = Field(None, description="The standardized sub-country region of the respondent")
    respondent_custom_fields: Dict[str, str] = Field({}, description="Any campaign-specific fields")