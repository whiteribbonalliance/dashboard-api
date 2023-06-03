from app.crud.campaign import CampaignCRUD
from app.enums.campaign_code import CampaignCode


def get_mapping_to_description(campaign_code: CampaignCode) -> dict:
    """Get mapping to description"""

    campaign_crud = CampaignCRUD(campaign_code=campaign_code)

    hierarchy = campaign_crud.get_category_hierarchy()
    mapping_to_description = {}
    for top_level, leaves in hierarchy.items():
        for code, name in leaves.items():
            mapping_to_description[code] = name

    return mapping_to_description


def get_mapping_to_top_level(campaign_code: CampaignCode) -> dict:
    """Get mapping to top level"""

    campaign_crud = CampaignCRUD(campaign_code=campaign_code)

    hierarchy = campaign_crud.get_category_hierarchy()
    mapping_to_top_level = {}
    for top_level, leaves in hierarchy.items():
        for code, name in leaves.items():
            mapping_to_top_level[code] = top_level

    return mapping_to_top_level
