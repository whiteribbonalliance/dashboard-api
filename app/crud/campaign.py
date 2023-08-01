"""
Reads/writes data from/to a campaign's databank
"""

import copy

import inflect
import pandas as pd

from app import databank
from app.enums.campaign_code import CampaignCode
from app.enums.question_code import QuestionCode
from app.schemas.age import Age
from app.schemas.country import Country
from app.schemas.gender import Gender
from app.schemas.profession import Profession
from app.schemas.region import Region

inflect_engine = inflect.engine()


class CampaignCRUD:
    def __init__(self, campaign_code: CampaignCode):
        self.__databank = databank.get_campaign_databank(campaign_code=campaign_code)

    def get_countries_list(self) -> list[Country]:
        """Get countries list"""

        countries = self.__databank.countries

        return copy.deepcopy(list(countries.values()))

    def get_countries_dict(self) -> dict[str, Country]:
        """Get countries dict"""

        countries = self.__databank.countries
        if countries:
            return copy.deepcopy(countries)

        return {}

    def get_country_regions(self, country_alpha2_code: str) -> list[Region]:
        """Get country regions"""

        countries = self.__databank.countries
        country = countries.get(country_alpha2_code)
        if country:
            return copy.deepcopy(country.regions)

        return []

    def get_ages(self) -> list[Age]:
        """Get ages"""

        ages = self.__databank.ages

        return copy.copy(ages)

    def get_genders(self) -> list[Gender]:
        """Get genders"""

        genders = self.__databank.genders

        return genders

    def get_professions(self) -> list[Profession]:
        """Get professions"""

        professions = self.__databank.professions

        return copy.copy(professions)

    def get_only_responses_from_categories_options(self) -> list[dict]:
        """Get only responses from categories options"""

        only_responses_from_categories_options = (
            self.__databank.only_responses_from_categories_options
        )

        return copy.deepcopy(only_responses_from_categories_options)

    def get_only_multi_word_phrases_containing_filter_term_options(self) -> list[dict]:
        """Get only multi-word phrases containing filter term options"""

        only_multi_word_phrases_containing_filter_term_options = (
            self.__databank.only_multi_word_phrases_containing_filter_term_options
        )

        return copy.deepcopy(only_multi_word_phrases_containing_filter_term_options)

    def get_responses_sample_columns(self) -> list[dict]:
        """Get responses sample columns"""

        responses_sample_columns = copy.deepcopy(
            self.__databank.responses_sample_columns
        )

        return responses_sample_columns

    def get_respondent_noun_singular(self) -> str:
        """Get respondent noun singular"""

        respondent_noun = copy.copy(self.__databank.respondent_noun)

        return respondent_noun

    def get_respondent_noun_plural(self) -> str:
        """Get respondent noun plural"""

        respondent_noun = self.__databank.respondent_noun

        respondent_noun_plural = inflect_engine.plural(respondent_noun)

        return copy.copy(respondent_noun_plural)

    def get_extra_stopwords(self) -> set[str]:
        """Get extra stopwords"""

        extra_stopwords = self.__databank.extra_stopwords

        return copy.copy(extra_stopwords)

    def get_ngrams_unfiltered(self, q_code: QuestionCode) -> tuple:
        """Get ngrams unfiltered"""

        ngrams_unfiltered = self.__databank.ngrams_unfiltered.get(q_code.value)

        if not ngrams_unfiltered:
            return ()

        unigram_count_dict = ngrams_unfiltered.get("unigram")
        bigram_count_dict = ngrams_unfiltered.get("bigram")
        trigram_count_dict = ngrams_unfiltered.get("trigram")

        return (
            copy.deepcopy(unigram_count_dict),
            copy.deepcopy(bigram_count_dict),
            copy.deepcopy(trigram_count_dict),
        )

    def get_category_hierarchy(self) -> dict:
        """Get category hierarchy"""

        category_hierarchy = self.__databank.category_hierarchy

        return copy.deepcopy(category_hierarchy)

    def get_dataframe(self) -> pd.DataFrame:
        """Get dataframe"""

        dataframe = self.__databank.dataframe.copy()

        return dataframe

    def set_ngrams_unfiltered(self, ngrams_unfiltered: dict, q_code: QuestionCode):
        """Set ngrams unfiltered"""

        self.__databank.ngrams_unfiltered[q_code.value] = ngrams_unfiltered

    def set_ages(self, ages: list[Age]):
        """Set ages"""

        self.__databank.ages = ages

    def set_countries(self, countries: dict[str, Country]):
        """Set countries"""

        self.__databank.countries = countries

    def set_genders(self, genders: list[Gender]):
        """Set genders"""

        self.__databank.genders = genders

    def set_professions(self, professions: list[Profession]):
        """Set professions"""

        self.__databank.professions = professions

    def set_dataframe(self, df: pd.DataFrame):
        """Set dataframe"""

        self.__databank.dataframe = df
