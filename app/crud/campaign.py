"""
Reads/writes data from/to a campaign's database
"""

import copy

import inflect
from pandas import DataFrame

from app import databases
from app.databases import Database
from app.enums.campaign_code import CampaignCode
from app.enums.question_code import QuestionCode
from app.schemas.age import Age
from app.schemas.age_range import AgeRange
from app.schemas.country import Country
from app.schemas.gender import Gender
from app.schemas.option import Option
from app.schemas.profession import Profession
from app.schemas.region import Region
from app.schemas.response_column import ResponseColumn

inflect_engine = inflect.engine()


class CampaignCRUD:
    def __init__(self, campaign_code: CampaignCode, db: Database = None):
        # If db is supplied, CRUD will read/write data to the db supplied instead
        if db:
            self.__db = db
        else:
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

    def get_ages(self) -> list[Age]:
        """Get ages"""

        ages = self.__db.ages
        if ages:
            return [x.copy() for x in ages if x]

        return []

    def get_age_ranges(self) -> list[AgeRange]:
        """Get age ranges"""

        age_ranges = self.__db.age_ranges
        if age_ranges:
            return [x.copy() for x in age_ranges if x]

        return []

    def get_age_ranges_default(self) -> list[AgeRange]:
        """Get age ranges default"""

        age_ranges_default = self.__db.age_ranges_default
        if age_ranges_default:
            return [x.copy() for x in age_ranges_default if x]

        return []

    def get_genders(self) -> list[Gender]:
        """Get genders"""

        genders = self.__db.genders
        if genders:
            return [x.copy() for x in genders if x]

        return []

    def get_professions(self) -> list[Profession]:
        """Get professions"""

        professions = self.__db.professions
        if professions:
            return [x.copy() for x in professions if x]

        return []

    def get_only_responses_from_categories_options(self) -> list[Option]:
        """Get only responses from categories options"""

        only_responses_from_categories_options = (
            self.__db.only_responses_from_categories_options
        )
        if only_responses_from_categories_options:
            return [x.copy() for x in only_responses_from_categories_options if x]

        return []

    def get_only_multi_word_phrases_containing_filter_term_options(
        self,
    ) -> list[Option]:
        """Get only multi-word phrases containing filter term options"""

        only_multi_word_phrases_containing_filter_term_options = (
            self.__db.only_multi_word_phrases_containing_filter_term_options
        )
        if only_multi_word_phrases_containing_filter_term_options:
            return [
                x.copy()
                for x in only_multi_word_phrases_containing_filter_term_options
                if x
            ]

        return []

    def get_responses_sample_columns(self) -> list[ResponseColumn]:
        """Get responses sample columns"""

        responses_sample_columns = self.__db.responses_sample_columns
        if responses_sample_columns:
            return [x.copy() for x in responses_sample_columns if x]

        return []

    def get_respondent_noun_singular(self) -> str:
        """Get respondent noun singular"""

        respondent_noun = self.__db.respondent_noun
        if respondent_noun:
            return respondent_noun

        return ""

    def get_respondent_noun_plural(self) -> str:
        """Get respondent noun plural"""

        respondent_noun = self.__db.respondent_noun
        if respondent_noun:
            respondent_noun_plural = inflect_engine.plural(respondent_noun)

            return respondent_noun_plural

        return ""

    def get_extra_stopwords(self) -> set[str]:
        """Get extra stopwords"""

        extra_stopwords = self.__db.extra_stopwords
        if extra_stopwords:
            return extra_stopwords.copy()

        return set()

    def get_category_hierarchy(self) -> dict[str, dict]:
        """Get category hierarchy"""

        category_hierarchy = self.__db.category_hierarchy
        if category_hierarchy:
            return copy.deepcopy(category_hierarchy)

        return {}

    def get_dataframe(self) -> DataFrame:
        """Get dataframe"""

        dataframe = self.__db.dataframe

        return dataframe.copy()

    def get_parent_categories_descriptions(self) -> dict[str, str]:
        """Get parent categories descriptions"""

        parent_categories_descriptions = self.__db.parent_categories_descriptions
        if parent_categories_descriptions:
            return parent_categories_descriptions.copy()

        return {}

    def get_ngrams_unfiltered(self, q_code: QuestionCode) -> tuple:
        """Get ngrams unfiltered"""

        ngrams_unfiltered = self.__db.ngrams_unfiltered.get(q_code.value)

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
        self, ngrams_unfiltered: dict[str, dict[str, int]], q_code: QuestionCode
    ):
        """Set ngrams unfiltered"""

        self.__db.ngrams_unfiltered[q_code.value] = ngrams_unfiltered

    def set_ages(self, ages: list[Age]):
        """Set ages"""

        self.__db.ages = ages

    def set_age_ranges(self, age_ranges: list[AgeRange]):
        """Set age ranges"""

        self.__db.age_ranges = age_ranges

    def set_age_ranges_default(self, age_ranges_default: list[AgeRange]):
        """Set age ranges default"""

        self.__db.age_ranges_default = age_ranges_default

    def set_countries(self, countries: dict[str, Country]):
        """Set countries"""

        self.__db.countries = countries

    def set_genders(self, genders: list[Gender]):
        """Set genders"""

        self.__db.genders = genders

    def set_professions(self, professions: list[Profession]):
        """Set professions"""

        self.__db.professions = professions

    def set_dataframe(self, df: DataFrame):
        """Set dataframe"""

        self.__db.dataframe = df
