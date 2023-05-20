from app.config import get_campaign_config


def get_unique_countries(campaign: str) -> list[dict]:
    """Get unique countries"""

    config = get_campaign_config(campaign)

    countries_list = config.countries_list
    unique_countries = []
    for alpha3code, country_name, demonym in countries_list:
        unique_countries.append({"value": alpha3code, "label": country_name})

    return unique_countries


def get_country_regions(campaign: str, country_alpha2_code: str) -> list[dict]:
    """Get country regions"""

    config = get_campaign_config(campaign=campaign)

    regions = [
        {"value": region, "label": region}
        for region in config.country_to_regions.get(country_alpha2_code)
    ]
    if regions:
        return regions

    return []
