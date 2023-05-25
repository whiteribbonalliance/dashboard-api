"""
Reads data from a databank
"""

import inflect
from pandas import DataFrame

from app.databank import get_campaign_databank
from app.enums.campaign_code import CampaignCode
from app.schemas.country import Country
from app.schemas.filter import Filter
from app.schemas.response_topic import ResponseTopic
from app.utils import code_hierarchy
from app.utils import filters

inflect_engine = inflect.engine()


class DataReader:
    def __init__(
        self,
        campaign_code: CampaignCode,
        filter_1: Filter = None,
        filter_2: Filter = None,
    ):
        self.__campaign_code = campaign_code
        self.__databank = get_campaign_databank(campaign_code=campaign_code)
        self.__filter_1 = filter_1
        self.__filter_2 = filter_2

    def get_dataframe_filtered(self, _filter: Filter) -> DataFrame:
        """Get dataframe filtered"""

        dataframe_copy = self.__databank.dataframe.copy()
        dataframe_filtered = filters.apply_filters(
            df_copy=dataframe_copy, _filter=_filter
        )

        return dataframe_filtered

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

    def get_only_responses_from_categories_options(self) -> list[dict[str, str]]:
        """Get only responses from categories options"""

        only_responses_from_categories_options = (
            self.__databank.only_responses_from_categories_options
        )

        return only_responses_from_categories_options

    def get_only_multi_word_phrases_containing_filter_term_options(
        self,
    ) -> list[dict[str, str]]:
        """Get only multi-word phrases containing filter term options"""

        only_multi_word_phrases_containing_filter_term_options = (
            self.__databank.only_multi_word_phrases_containing_filter_term_options
        )

        return only_multi_word_phrases_containing_filter_term_options

    def get_responses_sample_columns(self) -> list[dict[str, str]]:
        """Get responses sample columns"""

        responses_sample_columns = self.__databank.responses_sample_columns

        return responses_sample_columns

    def get_responses_sample_data(self):
        """Get responses data sample"""

        def get_all_descriptions(code: str):
            """Get all descriptions"""

            mapping_to_description = code_hierarchy.get_mapping_to_description(
                campaign_code=self.__campaign_code
            )

            return mapping_to_description.get(
                code,
                " / ".join(
                    sorted(
                        set([mapping_to_description.get(x, x) for x in code.split("/")])
                    )
                ),
            )

        df = self.__databank.dataframe

        # Apply filter to dataframe
        if self.__filter_1:
            df, description = filters.apply_filters(
                campaign_code=self.__campaign_code, df=df, _filter=self.__filter_1
            )

        # Get a sample of 1000
        n_sample = 1000
        if len(df.index) > 0:
            if len(df.index) < n_sample:
                n_sample = len(df.index)
            df = df.sample(n=n_sample, random_state=1)

        df["description"] = df["canonical_code"].apply(get_all_descriptions)

        column_ids = [col["id"] for col in self.get_responses_sample_columns()]

        responses_sample_data = df[column_ids].to_dict("records")

        return responses_sample_data

    def get_respondent_noun_singular(self):
        """Get respondent noun singular"""

        respondent_noun = self.__databank.respondent_noun

        return respondent_noun

    def get_respondent_noun_plural(self):
        """Get respondent noun plural"""

        respondent_noun = self.__databank.respondent_noun

        respondent_noun_plural = inflect_engine.plural(respondent_noun)

        return respondent_noun_plural
