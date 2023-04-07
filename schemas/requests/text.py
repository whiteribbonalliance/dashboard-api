from typing import List, Dict

from pydantic import BaseModel, Field

from schemas.enums.file_types import FileType
from schemas.enums.languages import Language


class CampaignResponse(BaseModel):
    campaign_id: str = Field(description="Unique identifier for the campaign")
    response_id: str = Field(None, description="Unique identifier for the response (UUID-4)")
    mobilizer_name: str = Field(None, description="The name of the mobilizer")
    mobilizer_id: str = Field(None, description="The ID of the mobilizer")
    contact_number: str = Field(None, description="The contact number of the mobilizer or respondent")
    is_consent: bool = Field(description="The consent to store data according to GDPR")
    respondent_name: str = Field(description="The name of the respondent")
    respondent_age: str = Field(None, description="The age of the respondent (either a value, a range, or N/A)")
    respondent_gender: str = Field(None, description="The gender of the respondent")
    respondent_country_code: str = Field(description="The alpha-2 country code of the respondent")
    respondent_region_code: str = Field(None, description="The standardized sub-country region of the respondent")
    respondent_custom_fields: Dict[str, str] = Field({}, description="Any campaign-specific fields")