from app.config import get_campaign_config


def get_mapping_to_description(campaign: str) -> dict:
    config = get_campaign_config(campaign)

    hierarchy = config.category_hierarchy
    mapping_to_description = {}
    for top_level, leaves in hierarchy.items():
        for code, name in leaves.items():
            mapping_to_description[code] = name

    return hierarchy


def get_mapping_to_top_level(campaign: str) -> dict:
    config = get_campaign_config(campaign)

    hierarchy = config.category_hierarchy
    mapping_to_top_level = {}
    for top_level, leaves in hierarchy.items():
        for code, name in leaves.items():
            mapping_to_top_level[code] = top_level

    return hierarchy


def get_response_topics(campaign: str) -> list[dict]:
    config = get_campaign_config(campaign)

    hierarchy = config.category_hierarchy
    response_topics = []
    for top_level, leaves in hierarchy.items():
        for code, name in leaves.items():
            response_topics.append({"value": code, "label": name})

    return response_topics
