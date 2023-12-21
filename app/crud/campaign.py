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

import copy

import inflect
from pandas import DataFrame

from app import databases
from app.databases import Database
from app.schemas.category import ParentCategory
from app.schemas.country import Country
from app.schemas.region import Region
from app.schemas.response_column import ResponseSampleColumn

inflect_engine = inflect.engine()


class Campaign:
    """
    Used for communication with the db object stored in memory.
    """

    def __init__(self, campaign_code: str, db: Database = None):
        if db:
            self.__db = db
        else:
            db = databases.get_campaign_db(campaign_code=campaign_code)
            if not db:
                raise Exception(f"Could not find db for {campaign_code}.")

            self.__db = databases.get_campaign_db(campaign_code=campaign_code)

    def get_countries_list(self) -> list[Country]:
        """Get countries list"""

        countries = self.__db.countries
        if countries:
            return [x.copy(deep=True) for x in list(countries.values()) if x]

        return []

    def get_countries_dict(self) -> dict[str, Country]:
        """Get countries dict"""

        countries = self.__db.countries
        if countries:
            return {k: v.copy(deep=True) for k, v in countries.items()}

        return {}

    def get_country_regions(self, country_alpha2_code: str) -> list[Region]:
        """Get country regions"""

        countries = self.__db.countries
        country = countries.get(country_alpha2_code)
        if country:
            return [x.copy() for x in country.regions if x]

        return []

    def get_q_codes(self) -> list[str]:
        """Get q codes"""

        q_codes = copy.copy(self.__db.q_codes)

        return q_codes

    def get_response_years(self) -> list[str]:
        """Get response years"""

        response_years = copy.copy(self.__db.response_years)

        return response_years

    def get_ages(self) -> list[str]:
        """Get ages"""

        ages = self.__db.ages
        if ages:
            return [x for x in ages if x]

        return []

    def get_age_buckets(self) -> list[str]:
        """Get age buckets"""

        age_buckets = self.__db.age_buckets
        if age_buckets:
            return [x for x in age_buckets if x]

        return []

    def get_age_buckets_default(self) -> list[str]:
        """Get age buckets default"""

        age_buckets_default = self.__db.age_buckets_default
        if age_buckets_default:
            return [x for x in age_buckets_default if x]

        return []

    def get_genders(self) -> list[str]:
        """Get genders"""

        genders = self.__db.genders
        if genders:
            return [x for x in genders if x]

        return []

    def get_living_settings(self) -> list[str]:
        """Get living settings"""

        living_settings = self.__db.living_settings
        if living_settings:
            return [x for x in living_settings if x]

        return []

    def get_professions(self) -> list[str]:
        """Get professions"""

        professions = self.__db.professions
        if professions:
            return [x for x in professions if x]

        return []

    def get_responses_sample_columns(self) -> list[ResponseSampleColumn]:
        """Get responses sample columns"""

        responses_sample_columns = self.__db.responses_sample_columns
        if responses_sample_columns:
            return [x.copy() for x in responses_sample_columns if x]

        return []

    def get_respondent_noun_singular(self) -> str:
        """Get respondent noun singular"""

        respondent_noun = self.__db.respondent_noun_singular
        if respondent_noun:
            return respondent_noun

        return ""

    def get_respondent_noun_plural(self) -> str:
        """Get respondent noun plural"""

        respondent_noun = self.__db.respondent_noun_singular
        if respondent_noun:
            respondent_noun_plural = inflect_engine.plural(respondent_noun)

            return respondent_noun_plural

        return ""

    # def get_category_hierarchy(self) -> dict[str, dict]:
    #     """Get category hierarchy"""
    #
    #     category_hierarchy = self.__db.category_hierarchy
    #     if category_hierarchy:
    #         return copy.deepcopy(category_hierarchy)
    #
    #     return {}

    def get_dataframe(self) -> DataFrame:
        """Get dataframe"""

        dataframe = self.__db.dataframe

        return dataframe.copy()

    def get_parent_categories(self) -> list[ParentCategory]:
        """Get parent categories"""

        parent_categories_descriptions = self.__db.parent_categories
        if parent_categories_descriptions:
            return parent_categories_descriptions.copy()

        return []

    def get_ngrams_unfiltered(self, q_code: str) -> tuple:
        """Get ngrams unfiltered"""

        ngrams_unfiltered = self.__db.ngrams_unfiltered.get(q_code)

        if not ngrams_unfiltered:
            return ()

        unigram_count_dict = ngrams_unfiltered.get("unigram")
        bigram_count_dict = ngrams_unfiltered.get("bigram")
        trigram_count_dict = ngrams_unfiltered.get("trigram")

        return (
            unigram_count_dict.copy(),
            bigram_count_dict.copy(),
            trigram_count_dict.copy(),
        )

    def set_ngrams_unfiltered(
        self, ngrams_unfiltered: dict[str, dict[str, int]], q_code: str
    ):
        """Set ngrams unfiltered"""

        self.__db.ngrams_unfiltered[q_code] = ngrams_unfiltered

    def set_response_years(self, response_years: list[str]):
        """Set response years"""

        self.__db.response_years = response_years

    def set_ages(self, ages: list[str]):
        """Set ages"""

        self.__db.ages = ages

    def set_age_buckets(self, age_buckets: list[str]):
        """Set age buckets"""

        self.__db.age_buckets = age_buckets

    def set_age_buckets_default(self, age_buckets_default: list[str]):
        """Set age buckets default"""

        self.__db.age_buckets_default = age_buckets_default

    def set_countries(self, countries: dict[str, Country]):
        """Set countries"""

        self.__db.countries = countries

    def set_genders(self, genders: list[str]):
        """Set genders"""

        self.__db.genders = genders

    def set_living_settings(self, living_settings: list[str]):
        """Set living settings"""

        self.__db.living_settings = living_settings

    def set_professions(self, professions: list[str]):
        """Set professions"""

        self.__db.professions = professions

    def set_dataframe(self, df: DataFrame):
        """Set dataframe"""

        self.__db.dataframe = df

    def set_q_codes(self, q_codes: list[str]):
        """Set q codes"""

        self.__db.q_codes = q_codes
