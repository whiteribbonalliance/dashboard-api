"""
Reads data from a databank
"""

from app.databank import get_campaign_databank
from app.schemas.country import Country
from app.schemas.response_topic import ResponseTopic


def get_countries_list(campaign: str) -> list[Country]:
    """Get countries list"""

    databank = get_campaign_databank(campaign=campaign)

    countries = databank.countries

    return list(countries.values())


def get_countries_dict(campaign: str) -> dict[str, Country]:
    """Get countries dict"""

    databank = get_campaign_databank(campaign=campaign)

    countries = databank.countries
    if countries:
        return countries

    return {}


def get_country_regions(campaign: str, country_alpha2_code: str) -> list[str]:
    """Get country regions"""

    databank = get_campaign_databank(campaign=campaign)

    countries = databank.countries
    country = countries.get(country_alpha2_code)
    if country:
        return country.regions

    return []


def get_response_topics(campaign: str) -> list[ResponseTopic]:
    """Get response topics"""

    databank = get_campaign_databank(campaign=campaign)

    hierarchy = databank.category_hierarchy
    response_topics = []
    for top_level, leaves in hierarchy.items():
        for code, name in leaves.items():
            response_topics.append(ResponseTopic(code=code, name=name))

    return response_topics


def get_age_buckets(campaign: str) -> list[str]:
    """Get age buckets"""

    databank = get_campaign_databank(campaign=campaign)

    age_buckets = databank.age_buckets

    return age_buckets
