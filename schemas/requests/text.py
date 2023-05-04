from datetime import date
from typing import Dict, Any
from pydantic import BaseModel, Field


class CampaignResponse(BaseModel):
    campaign: str = Field(
        description="Unique identifier for the campaign",
    )

    mobilizer_name: str = Field(None, description="The name of the mobilizer")
    mobilizer_contact_number: int = Field(None, description="The contact number/phone number/ID of the mobilizer")

    respondent_additional_fields: Dict[str, Any] = Field(None, description="Any campaign or respondent-specific fields")
    respondent_age: int = Field(None, description="The age of the respondent (either a value, a range, or N/A)")
    respondent_age_bucket: str = Field(None, description="The age of the respondent (a pre-defined range, 'prefer not to say', or N/A)")
    respondent_contact_number: int = Field(None, description="The contact number/phone number/ID of the respondent")
    respondent_gender: str = Field(None, description="The gender of the respondent")
    respondent_country_code: str = Field(None, description="The alpha-2 country code of the respondent")
    respondent_id: str = Field(None, description="Unique identifier for the response (UUID-4)")
    respondent_language: str = Field(None, description="The primary language of the respondent")
    respondent_name: str = Field(None, description="The name of the respondent")
    respondent_region_code: str = Field(None, description="The standardized sub-country region of the respondent")
    respondent_region_name: str = Field(None, description="The free-text sub-country region of the respondent")

    response_consent: bool = Field(None, description="The consent to store data according to GDPR")
    response_date: date = Field(None, description="The date the reponse was submitted")
    response_free_text: str = Field(
        None, description="The main free-text response of the survey, always in English. (translated into English by ETL if needed)"
    )
    response_original_lang: str = Field(None, description="Language code of the original response. Set by ETL")
    response_original_text: str = Field(None, description="Main original free-text response of the survey, if it was not in English")
    response_nlu_category: str = Field(None, description="Main response category as detected by the NLU pipeline")
    response_nlu_confidence: float = Field(None, description="Main response category confidence as detected by the NLU pipeline")
    source: str = Field(None, description="Where the data came from")
