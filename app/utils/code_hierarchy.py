from app.crud.campaign import CampaignCRUD
from app.enums.campaign_code import CampaignCode


def get_mapping_code_to_code(campaign_code: CampaignCode) -> dict:
    """Get mapping 'code to code'"""

    campaign_crud = CampaignCRUD(campaign_code=campaign_code)

    hierarchy = campaign_crud.get_category_hierarchy()
    mapping_code_to_code = {}
    for parent_category, sub_categories in hierarchy.items():
        mapping_code_to_code[parent_category] = parent_category
        for code, description in sub_categories.items():
            mapping_code_to_code[code] = code

    return mapping_code_to_code


def get_mapping_code_to_description(campaign_code: CampaignCode) -> dict:
    """Get mapping 'code to description'"""

    campaign_crud = CampaignCRUD(campaign_code=campaign_code)

    category_hierarchy = campaign_crud.get_category_hierarchy()
    mapping_code_to_description = {}
    for parent_category, sub_categories in category_hierarchy.items():
        mapping_code_to_description[parent_category] = parent_category
        for code, description in sub_categories.items():
            mapping_code_to_description[code] = description

    return mapping_code_to_description


def get_mapping_code_to_parent_category(campaign_code: CampaignCode) -> dict:
    """Get mapping 'code to parent category'"""

    campaign_crud = CampaignCRUD(campaign_code=campaign_code)

    category_hierarchy = campaign_crud.get_category_hierarchy()
    mapping_code_to_parent_category = {}
    for parent_category, sub_categories in category_hierarchy.items():
        mapping_code_to_parent_category[parent_category] = parent_category
        for code, description in sub_categories.items():
            mapping_code_to_parent_category[code] = parent_category

    return mapping_code_to_parent_category
