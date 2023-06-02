from app.constants import CAMPAIGNS_LIST
from app.enums.campaign_code import CampaignCode
from app.http_exceptions import ResourceNotFoundHTTPException


async def common_parameters(campaign: str) -> dict[str, CampaignCode]:
    """Verify the campaign and return the common parameter"""

    def verify_campaign() -> CampaignCode:
        """Check if campaign exists, If not, raise an exception"""

        if campaign.lower() not in [c.lower() for c in CAMPAIGNS_LIST]:
            raise ResourceNotFoundHTTPException("Campaign not found")

        if campaign == CampaignCode.what_women_want:
            return CampaignCode.what_women_want
        if campaign == CampaignCode.what_young_people_want:
            return CampaignCode.what_young_people_want
        if campaign == CampaignCode.midwives_voices:
            return CampaignCode.midwives_voices

    campaign_code_verified = verify_campaign()

    return {"campaign_code": campaign_code_verified}
