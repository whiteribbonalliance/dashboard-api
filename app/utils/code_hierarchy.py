"""
MIT License

Copyright (c) 2023 White Ribbon Alliance. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

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
    parent_categories_descriptions = campaign_crud.get_parent_categories_descriptions()

    category_hierarchy = campaign_crud.get_category_hierarchy()
    mapping_code_to_description = {}
    for parent_category, sub_categories in category_hierarchy.items():
        mapping_code_to_description[
            parent_category
        ] = parent_categories_descriptions.get(parent_category, parent_category)
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
