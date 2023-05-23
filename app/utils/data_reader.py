"""
Reads data from a databank
"""

from app.databank import get_campaign_databank
from app.enums.campaign_code import CampaignCode
from app.schemas.country import Country
from app.schemas.response_topic import ResponseTopic


class DataReader:
    def __init__(self, campaign_code: CampaignCode):
        self.__databank = get_campaign_databank(campaign_code=campaign_code)

    def get_countries_list(self) -> list[Country]:
        """Get countries list"""

        countries = self.__databank.countries

        return list(countries.values())

    def get_countries_dict(self) -> dict[str, Country]:
        """Get countries dict"""

        countries = self.__databank.countries
        if countries:
            return countries

        return {}

    def get_country_regions(self, country_alpha2_code: str) -> list[str]:
        """Get country regions"""

        countries = self.__databank.countries
        country = countries.get(country_alpha2_code)
        if country:
            return country.regions

        return []

    def get_response_topics(self) -> list[ResponseTopic]:
        """Get response topics"""

        hierarchy = self.__databank.category_hierarchy
        response_topics = []
        for top_level, leaves in hierarchy.items():
            for code, name in leaves.items():
                response_topics.append(ResponseTopic(code=code, name=name))

        return response_topics

    def get_age_buckets(self) -> list[str]:
        """Get age buckets"""

        age_buckets = self.__databank.age_buckets

        return age_buckets

    def get_genders(self) -> list[str]:
        """Get genders"""

        genders = self.__databank.genders

        return genders

    def get_professions(self) -> list[str]:
        """Get professions"""

        professions = self.__databank.professions

        return professions
