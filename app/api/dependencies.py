from app import constants
from app.constants import CAMPAIGN_CODES
from app.enums.campaign_code import CampaignCode
from app.http_exceptions import ResourceNotFoundHTTPException
from app.schemas.common_parameters import CommonParameters


async def common_parameters(campaign: str, lang: str = "en") -> CommonParameters:
    """Return the common parameters"""

    def verify_campaign() -> CampaignCode:
        """Verify campaign, If it doesn't exist, raise an exception"""

        if campaign.lower() not in [c.lower() for c in CAMPAIGN_CODES]:
            raise ResourceNotFoundHTTPException("Campaign not found")

        if campaign == CampaignCode.what_women_want:
            return CampaignCode.what_women_want
        if campaign == CampaignCode.what_young_people_want:
            return CampaignCode.what_young_people_want
        if campaign == CampaignCode.midwives_voices:
            return CampaignCode.midwives_voices

    def check_language() -> str:
        """Check if language exists, If not, default to 'en'"""

        if lang in constants.TRANSLATION_LANGUAGES:
            return lang
        else:
            return "en"

    campaign_code_verified = verify_campaign()
    language_verified = check_language()

    return CommonParameters(
        campaign_code=campaign_code_verified, language=language_verified
    )
