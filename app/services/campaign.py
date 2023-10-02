"""
Handles processing of data and business logic for a campaign
"""

import logging
import operator
import random
from collections import Counter

import numpy as np
import pandas as pd

from app import constants, helpers
from app import global_variables
from app.crud.campaign import CampaignCRUD
from app.enums.campaign_code import CampaignCode
from app.enums.question_code import QuestionCode
from app.logginglib import init_custom_logger
from app.schemas.age import Age
from app.schemas.age_bucket import AgeBucket
from app.schemas.campaign import Campaign
from app.schemas.country import Country
from app.schemas.filter import Filter
from app.schemas.filter_options import FilterOptions
from app.schemas.gender import Gender
from app.schemas.option import Option
from app.schemas.profession import Profession
from app.schemas.response_column import ResponseColumn
from app.schemas.response_topic import ResponseTopic
from app.services import googlemaps_interactions
from app.services.translations_cache import TranslationsCache
from app.services.translator import Translator
from app.types import FilterSequence
from app.utils import code_hierarchy
from app.utils import filters
from app.utils import q_col_names

logger = logging.getLogger(__name__)
init_custom_logger(logger)


class CampaignService:
    def __init__(
        self,
        campaign_code: CampaignCode,
        language: str = "en",
        response_year: str = None,
        filter_1: Filter = None,
        filter_2: Filter = None,
    ):
        # Campaign code
        self.__campaign_code = campaign_code

        # CRUD
        self.__crud = CampaignCRUD(campaign_code=self.__campaign_code)

        # Language
        self.__language = language

        # All response years
        self.__all_response_years = self.__get_response_years()

        # Response year
        if response_year and response_year in self.__all_response_years:
            self.__response_year = response_year
        else:
            self.__response_year = None

        # Filters
        self.__filter_1 = filter_1
        self.__filter_2 = filter_2

        # Get dataframe
        df = self.__crud.get_dataframe()

        # For 'wwwpakistan' filter the response year
        if (
            self.__campaign_code == CampaignCode.what_women_want_pakistan
            and self.__response_year
        ):
            df = df[df["response_year"] == self.__response_year]

        # Apply filter 1
        if self.__filter_1:
            self.__df_1 = filters.apply_filter_to_df(
                df=df.copy(),
                _filter=self.__filter_1,
                crud=self.__crud,
            )
        else:
            self.__df_1 = df.copy()

        # Apply filter 2
        if self.__filter_2:
            self.__df_2 = filters.apply_filter_to_df(
                df=df.copy(),
                _filter=self.__filter_2,
                crud=self.__crud,
            )
        else:
            self.__df_2 = df.copy()

        # Filter 1 description
        self.__filter_1_description = self.__get_df_filter_description(
            df_len=len(self.__df_1), _filter=self.__filter_1
        )

        # Filter 2 description
        self.__filter_2_description = self.__get_df_filter_description(
            df_len=len(self.__df_2), _filter=self.__filter_2
        )

        # If filter 1 was requested, then do not use the cached ngrams
        self.__filter_1_use_ngrams_unfiltered = True
        if self.__filter_1 and not filters.check_if_filter_is_default(
            _filter=self.__filter_1
        ):
            self.__filter_1_use_ngrams_unfiltered = False

        # If filter 2 was requested, then do not use the cached ngrams
        self.__filter_2_use_ngrams_unfiltered = True
        if self.__filter_2 and not filters.check_if_filter_is_default(
            _filter=self.__filter_2
        ):
            self.__filter_2_use_ngrams_unfiltered = False

        # Campaign question codes
        self.__campaign_q_codes = self.__crud.get_q_codes()

        # Ngrams
        self.__ngrams_1 = {}
        self.__ngrams_2 = {}
        for q_code in self.__campaign_q_codes:
            # Ngrams 1
            if self.__filter_1:
                self.__ngrams_1[q_code.value] = self.__get_ngrams_1(
                    only_multi_word_phrases_containing_filter_term=self.__filter_1.only_multi_word_phrases_containing_filter_term,
                    keyword=self.__filter_1.keyword_filter,
                    q_code=q_code,
                )
            else:
                self.__ngrams_1[q_code.value] = self.__get_ngrams_1(
                    only_multi_word_phrases_containing_filter_term=False,
                    keyword="",
                    q_code=q_code,
                )

            # Ngrams 2
            self.__ngrams_2[q_code.value] = self.__get_ngrams_2(q_code=q_code)

        # Check if filters are identical or not
        self.__filters_are_identical = filters.check_if_filters_are_identical(
            filter_1=filter_1, filter_2=filter_2
        )

        # Get unique parent categories from response_topics
        self.__response_topics_unique_parent_categories = (
            self.__get_unique_parent_categories_from_response_topics()
        )

    def get_campaign(
        self,
        q_code: QuestionCode,
        include_list_of_ages: bool = False,
        include_list_of_age_buckets_default: bool = False,
    ) -> Campaign:
        """Get campaign"""

        # Included response years
        if self.__response_year:
            included_response_years = [self.__response_year]
        else:
            included_response_years = self.__all_response_years

        # Top words and phrases
        top_words_and_phrases = {
            "top_words": self.__get_top_words(q_code=q_code),
            "two_word_phrases": self.__get_two_word_phrases(q_code=q_code),
            "three_word_phrases": self.__get_three_word_phrases(q_code=q_code),
            "wordcloud_words": self.__get_wordcloud_words(q_code=q_code),
        }

        # Responses sample
        responses_sample = {
            "columns": [
                x.dict() for x in self.__get_responses_sample_columns(q_code=q_code)
            ],
            "data": self.__get_responses_sample(q_code=q_code),
        }

        # Responses breakdown
        responses_breakdown = self.__get_responses_breakdown(q_code=q_code)

        # Living settings breakdown
        living_settings_breakdown = self.__get_living_settings_breakdown()

        # Histogram
        histogram = self.__get_histogram()

        # Genders breakdown
        if (
            self.__campaign_code == CampaignCode.what_young_people_want
            or self.__campaign_code == CampaignCode.healthwellbeing
        ):
            genders_breakdown = self.__get_genders_breakdown()
        else:
            genders_breakdown = []

        # World bubble maps coordinates
        world_bubble_maps_coordinates = self.__get_world_bubble_maps_coordinates()

        # List of ages
        if include_list_of_ages and q_code == QuestionCode.q1:
            list_of_ages_1 = self.__get_list_of_ages(filter_seq="1")
            list_of_ages_2 = self.__get_list_of_ages(filter_seq="2")
        else:
            list_of_ages_1 = []
            list_of_ages_2 = []

        # List of age buckets
        if include_list_of_age_buckets_default and q_code == QuestionCode.q1:
            list_of_age_buckets_1 = self.__get_list_of_age_buckets_default(
                filter_seq="1"
            )
            list_of_age_buckets_2 = self.__get_list_of_age_buckets_default(
                filter_seq="2"
            )
        else:
            list_of_age_buckets_1 = []
            list_of_age_buckets_2 = []

        # Respondents count
        filter_1_respondents_count = self.__get_filter_respondents_count(filter_seq="1")
        filter_2_respondents_count = self.__get_filter_respondents_count(filter_seq="2")

        # Average age
        filter_1_average_age = self.__get_filter_average_age(filter_seq="1")
        filter_2_average_age = self.__get_filter_average_age(filter_seq="2")
        filter_1_average_age_bucket = self.__get_filter_average_age_bucket(
            filter_seq="1"
        )
        filter_2_average_age_bucket = self.__get_filter_average_age_bucket(
            filter_seq="2"
        )

        # Filters Description
        filter_1_description = self.__get_filter_description(filter_seq="1")
        filter_2_description = self.__get_filter_description(filter_seq="2")

        # Filters are identical
        filters_are_identical = self.__get_filters_are_identical()

        # Question codes
        all_q_codes = [x.value for x in self.__crud.get_q_codes()]

        # Translate
        try:
            if self.__language != "en" and TranslationsCache().is_loaded():
                translator = Translator()
                translator.set_target_language(target_language=self.__language)

                # Extract texts
                translator.apply_t_function_campaign(
                    t=translator.extract_text,
                    campaign_code=self.__campaign_code,
                    language=self.__language,
                    responses_sample=responses_sample,
                    responses_breakdown=responses_breakdown,
                    living_settings_breakdown=living_settings_breakdown,
                    top_words_and_phrases=top_words_and_phrases,
                    histogram=histogram,
                    genders_breakdown=genders_breakdown,
                    world_bubble_maps_coordinates=world_bubble_maps_coordinates,
                    filter_1_average_age=filter_1_average_age,
                    filter_2_average_age=filter_2_average_age,
                    filter_1_description=filter_1_description,
                    filter_2_description=filter_2_description,
                )

                # Translate extracted texts
                translator.translate_extracted_texts()

                # Apply translations to texts
                (
                    responses_sample,
                    responses_breakdown,
                    living_settings_breakdown,
                    top_words_and_phrases,
                    histogram,
                    genders_breakdown,
                    world_bubble_maps_coordinates,
                    filter_1_average_age,
                    filter_2_average_age,
                    filter_1_description,
                    filter_2_description,
                ) = translator.apply_t_function_campaign(
                    t=translator.translate_text,
                    campaign_code=self.__campaign_code,
                    language=self.__language,
                    responses_sample=responses_sample,
                    responses_breakdown=responses_breakdown,
                    living_settings_breakdown=living_settings_breakdown,
                    top_words_and_phrases=top_words_and_phrases,
                    histogram=histogram,
                    genders_breakdown=genders_breakdown,
                    world_bubble_maps_coordinates=world_bubble_maps_coordinates,
                    filter_1_average_age=filter_1_average_age,
                    filter_2_average_age=filter_2_average_age,
                    filter_1_description=filter_1_description,
                    filter_2_description=filter_2_description,
                )
        except (Exception,) as e:
            logger.warning(
                f"An error occurred during translation of 'campaign': {str(e)}"
            )

        return Campaign(
            campaign_code=self.__campaign_code.value,
            q_code=q_code.value,
            all_q_codes=all_q_codes,
            included_response_years=included_response_years,
            all_response_years=self.__all_response_years,
            responses_sample=responses_sample,
            responses_breakdown=responses_breakdown,
            living_settings_breakdown=living_settings_breakdown,
            top_words_and_phrases=top_words_and_phrases,
            histogram=histogram,
            genders_breakdown=genders_breakdown,
            world_bubble_maps_coordinates=world_bubble_maps_coordinates,
            list_of_ages_1=list_of_ages_1,
            list_of_ages_2=list_of_ages_2,
            list_of_age_buckets_1=list_of_age_buckets_1,
            list_of_age_buckets_2=list_of_age_buckets_2,
            filter_1_respondents_count=filter_1_respondents_count,
            filter_2_respondents_count=filter_2_respondents_count,
            filter_1_average_age=filter_1_average_age,
            filter_2_average_age=filter_2_average_age,
            filter_1_average_age_bucket=filter_1_average_age_bucket,
            filter_2_average_age_bucket=filter_2_average_age_bucket,
            filter_1_description=filter_1_description,
            filter_2_description=filter_2_description,
            filters_are_identical=filters_are_identical,
        )

    def get_filter_options(self) -> FilterOptions:
        """Get filter options"""

        # Country options
        countries = self.__get_countries_list()
        country_options = [
            Option(value=country.alpha2_code, label=country.name).dict()
            for country in countries
        ]

        # Region options and province options
        country_region_options: list[dict[str, str | list[Option]]] = []
        country_province_options: list[dict[str, str | list[Option]]] = []
        for country in countries:
            region_options = {
                "country_alpha2_code": country.alpha2_code,
                "options": [],
            }
            province_options = {
                "country_alpha2_code": country.alpha2_code,
                "options": [],
            }

            provinces_found = set()
            for region in sorted(country.regions, key=lambda r: r.name):
                # Region
                region_options["options"].append(
                    Option(value=region.code, label=region.name).dict()
                )

                # Province
                if region.province and region.province not in provinces_found:
                    province_options["options"].append(
                        Option(value=region.province, label=region.province).dict()
                    )
                    provinces_found.add(region.province)

            country_region_options.append(region_options)
            country_province_options.append(province_options)

        # Response topic options
        response_topics = self.__get_response_topics()
        response_topic_options = [
            Option(
                value=response_topic.code,
                label=response_topic.name,
                metadata="is_parent" if response_topic.is_parent else "",
            ).dict()
            for response_topic in response_topics
        ]

        # Age options
        ages = self.__get_ages()
        age_options = [Option(value=age.code, label=age.name).dict() for age in ages]

        # Age bucket options
        age_buckets = self.__get_age_buckets()
        age_bucket_options = [
            Option(value=age_bucket.code, label=age_bucket.name).dict()
            for age_bucket in age_buckets
        ]

        # Age buckets default options
        age_buckets_default = self.__get_age_buckets_default()
        age_bucket_default_options = [
            Option(value=age_bucket_default.code, label=age_bucket_default.name).dict()
            for age_bucket_default in age_buckets_default
        ]

        # Gender options
        genders = self.__get_genders()
        gender_options = [
            Option(value=gender.code, label=gender.name).dict() for gender in genders
        ]

        # Profession options
        professions = self.__get_professions()
        profession_options = [
            Option(value=profession.code, label=profession.name).dict()
            for profession in professions
        ]

        # Only responses from categories options
        only_responses_from_categories_options = [
            x.dict() for x in self.__get_only_responses_from_categories_options()
        ]

        # Only multi-word phrases containing filter term options
        only_multi_word_phrases_containing_filter_term_options = [
            x.dict()
            for x in self.__get_only_multi_word_phrases_containing_filter_term_options()
        ]

        # Translate
        try:
            if self.__language != "en" and TranslationsCache().is_loaded():
                translator = Translator()
                translator.set_target_language(target_language=self.__language)

                # Extract texts
                translator.apply_t_filter_options(
                    t=translator.extract_text,
                    country_options=country_options,
                    country_regions_options=country_region_options,
                    country_provinces_options=country_province_options,
                    response_topic_options=response_topic_options,
                    age_options=age_options,
                    age_bucket_options=age_bucket_options,
                    age_bucket_default_options=age_bucket_default_options,
                    gender_options=gender_options,
                    profession_options=profession_options,
                    only_responses_from_categories_options=only_responses_from_categories_options,
                    only_multi_word_phrases_containing_filter_term_options=only_multi_word_phrases_containing_filter_term_options,
                )

                # Translate extracted texts
                translator.translate_extracted_texts()

                # Apply translations to texts
                (
                    country_options,
                    country_region_options,
                    country_province_options,
                    response_topic_options,
                    age_options,
                    age_bucket_options,
                    age_bucket_default_options,
                    gender_options,
                    profession_options,
                    only_responses_from_categories_options,
                    only_multi_word_phrases_containing_filter_term_options,
                ) = translator.apply_t_filter_options(
                    t=translator.translate_text,
                    country_options=country_options,
                    country_regions_options=country_region_options,
                    country_provinces_options=country_province_options,
                    response_topic_options=response_topic_options,
                    age_options=age_options,
                    age_bucket_options=age_bucket_options,
                    age_bucket_default_options=age_bucket_default_options,
                    gender_options=gender_options,
                    profession_options=profession_options,
                    only_responses_from_categories_options=only_responses_from_categories_options,
                    only_multi_word_phrases_containing_filter_term_options=only_multi_word_phrases_containing_filter_term_options,
                )
        except (Exception,) as e:
            logger.warning(
                f"An error occurred during translation of 'filter_options': {str(e)}"
            )

        return FilterOptions(
            countries=country_options,
            country_regions=country_region_options,
            country_provinces=country_province_options,
            response_topics=response_topic_options,
            ages=age_options,
            age_buckets=age_bucket_options,
            age_buckets_default=age_bucket_default_options,
            genders=gender_options,
            professions=profession_options,
            only_responses_from_categories=only_responses_from_categories_options,
            only_multi_word_phrases_containing_filter_term=only_multi_word_phrases_containing_filter_term_options,
        )

    def get_who_the_people_are_options(self) -> list[Option]:
        """Get who the people are options"""

        breakdown_country_option = Option(
            value="breakdown-country",
            label=f"{'Show breakdown by country'}",
        )
        breakdown_age_option = Option(
            value="breakdown-age",
            label=f"{'Show breakdown by age'}",
        )
        breakdown_age_bucket_option = Option(
            value="breakdown-age-bucket",
            label="Show breakdown by age bucket",
        )
        breakdown_gender_option = Option(
            value="breakdown-gender",
            label=f"{'Show breakdown by gender'}",
        )
        breakdown_profession_option = Option(
            value="breakdown-profession",
            label=f"{'Show breakdown by profession'}",
        )

        options: list[Option] = []

        if self.__campaign_code == CampaignCode.what_women_want:
            options = [breakdown_age_bucket_option, breakdown_country_option]
        elif self.__campaign_code == CampaignCode.what_young_people_want:
            options = [
                breakdown_age_option,
                breakdown_gender_option,
                breakdown_country_option,
            ]
        elif self.__campaign_code == CampaignCode.midwives_voices:
            options = [
                breakdown_age_bucket_option,
                breakdown_profession_option,
                breakdown_country_option,
            ]
        elif self.__campaign_code == CampaignCode.healthwellbeing:
            options = [
                breakdown_age_option,
                breakdown_age_bucket_option,
                breakdown_country_option,
            ]
        elif self.__campaign_code == CampaignCode.economic_empowerment_mexico:
            options = [breakdown_age_bucket_option]
        elif self.__campaign_code == CampaignCode.what_women_want_pakistan:
            options = [breakdown_age_bucket_option]

        # Translate
        try:
            if self.__language != "en" and TranslationsCache().is_loaded():
                translator = Translator()
                translator.set_target_language(target_language=self.__language)

                # Extract texts
                translator.apply_t_who_the_people_are_options(
                    translator.extract_text, options=options
                )

                # Translate extracted texts
                translator.translate_extracted_texts()

                # Apply translations to texts
                options = translator.apply_t_who_the_people_are_options(
                    translator.translate_text, options=options
                )
        except (Exception,) as e:
            logger.warning(
                f"An error occurred during translation of 'who_the_people_are_options': {str(e)}"
            )

        return options

    def __get_unique_parent_categories_from_response_topics(self) -> set:
        """
        Get unique parent categories from response topics
        Will also check for the parent category of sub-categories
        """

        parent_categories = set()

        mapping_code_to_parent_category = (
            code_hierarchy.get_mapping_code_to_parent_category(
                campaign_code=self.__campaign_code
            )
        )

        if self.__filter_1:
            for category in self.__filter_1.response_topics:
                parent_category = mapping_code_to_parent_category.get(category)
                if parent_category:
                    parent_categories.add(parent_category)

        if self.__filter_2:
            for category in self.__filter_2.response_topics:
                parent_category = mapping_code_to_parent_category.get(category)
                if parent_category:
                    parent_categories.add(parent_category)

        return parent_categories

    def __get_responses_sample_columns(
        self, q_code: QuestionCode
    ) -> list[ResponseColumn]:
        """Get responses sample columns"""

        responses_sample_columns = self.__crud.get_responses_sample_columns()

        # For 'healthwellbeing' remove 'description' column if q2
        if (
            self.__campaign_code == CampaignCode.healthwellbeing
            and q_code == QuestionCode.q2
        ):
            responses_sample_columns = [
                x for x in responses_sample_columns if x.id != "description"
            ]

        return responses_sample_columns

    def __get_responses_sample(self, q_code: QuestionCode) -> list[dict]:
        """Get responses sample"""

        # Get copy to not modify original
        df_1_copy = self.__get_df_1_copy()

        response_sample_1 = self.__get_df_responses_sample(df=df_1_copy, q_code=q_code)

        # Only set responses_sample_2 if filter 2 was applied
        if self.__filter_2:
            # Get copy to not modify original
            df_2_copy = self.__get_df_2_copy()

            response_sample_2 = self.__get_df_responses_sample(
                df=df_2_copy, q_code=q_code
            )
        else:
            response_sample_2 = []

        responses_sample = response_sample_1 + response_sample_2

        # Shuffle
        random.shuffle(responses_sample)

        return responses_sample

    def __get_responses_sample_column_ids(
        self, q_code: QuestionCode = None
    ) -> list[str]:
        """Get responses sample column ids"""

        columns = self.__crud.get_responses_sample_columns()

        if not q_code:
            return [col.id for col in columns]

        # Rename column e.g. 'raw_response' -> 'q1_raw_response'
        for column in columns:
            if column.id == "raw_response":
                column.id = f"{q_code.value}_raw_response"
            if column.id == "description":
                column.id = f"{q_code.value}_description"

        return [col.id for col in columns]

    def __get_code_descriptions(self, code: str) -> str:
        """Get code descriptions"""

        mapping_to_description = code_hierarchy.get_mapping_code_to_description(
            campaign_code=self.__campaign_code
        )

        descriptions = mapping_to_description.get(
            code,
            " / ".join(
                sorted(
                    set(
                        [
                            mapping_to_description.get(x.strip(), x.strip())
                            for x in code.split("/")
                        ]
                    )
                )
            ),
        )

        return descriptions

    def __get_df_responses_sample(
        self, df: pd.DataFrame, q_code: QuestionCode
    ) -> list[dict]:
        """Get df responses sample"""

        # Set column names based on question code
        description_col_name = q_col_names.get_description_col_name(q_code=q_code)
        canonical_code_col_name = q_col_names.get_canonical_code_col_name(q_code=q_code)
        raw_response_col_name = q_col_names.get_raw_response_col_name(q_code=q_code)

        # Remove rows were raw_response is empty
        df = df[df[raw_response_col_name] != ""]

        # Limit the sample for languages that are not English
        if self.__language == "en":
            if self.__filter_2:
                n_sample = constants.n_responses_sample // 2  # 500
            else:
                n_sample = constants.n_responses_sample  # 1000
        else:
            if self.__filter_2:
                n_sample = constants.n_responses_sample // 2 // 10  # 50
            else:
                n_sample = constants.n_responses_sample // 10  # 100

        if len(df.index) > 0:
            if len(df.index) < n_sample:
                n_sample = len(df.index)
            df = df.sample(n=n_sample, random_state=1)
        else:
            return []

        column_ids = self.__get_responses_sample_column_ids(q_code=q_code)

        df[description_col_name] = df[canonical_code_col_name].apply(
            lambda x: self.__get_code_descriptions(x)
        )

        # Rename columns e.g. 'q1_raw_response' -> 'raw_response'
        columns_to_rename = {x: x.replace(f"{q_code.value}_", "") for x in column_ids}
        df = df.rename(columns=columns_to_rename)

        responses_sample_data: list[dict] = df[columns_to_rename.values()].to_dict(
            "records"
        )

        return responses_sample_data

    def __get_responses_breakdown(self, q_code: QuestionCode) -> dict[str, list]:
        """Get responses breakdown"""

        # Set column names based on question code
        canonical_code_col_name = q_col_names.get_canonical_code_col_name(q_code=q_code)
        label_col_name = q_col_names.get_label_col_name(q_code=q_code)
        count_col_name = q_col_names.get_count_col_name(q_code=q_code)
        code_col_name = q_col_names.get_code_col_name(q_code=q_code)
        description_col_name = q_col_names.get_description_col_name(q_code=q_code)
        parent_category_col_name = q_col_names.get_parent_category_col_name(
            q_code=q_code
        )

        def category_counter_to_responses_breakdown_data(
            category_counter: Counter,
        ) -> list[dict]:
            """Category counter to responses breakdown data"""

            if len(category_counter) > 0:
                # Create dataframe with items from counter
                df = pd.DataFrame(
                    sorted(
                        category_counter.items(),
                        key=operator.itemgetter(1),
                        reverse=True,
                    )
                )

                # Set column names
                df.columns = [label_col_name, count_col_name]

                # Set code
                df[code_col_name] = df[label_col_name].map(
                    code_hierarchy.get_mapping_code_to_code(
                        campaign_code=self.__campaign_code
                    )
                )

                # Set description column
                df[description_col_name] = df[label_col_name].map(
                    code_hierarchy.get_mapping_code_to_description(
                        campaign_code=self.__campaign_code
                    )
                )

                # Drop label column
                df = df.drop([label_col_name], axis=1)

                # Drop rows with nan values
                df = df.dropna()

                # what_young_people_want: Sort the rows by count value (DESC) and keep the first n rows only
                if self.__campaign_code == CampaignCode.what_young_people_want:
                    n_rows_keep = 5
                    df = df.sort_values(by=count_col_name, ascending=False)
                    df = df.head(n_rows_keep)
            else:
                df = pd.DataFrame()

            responses_breakdown_data = df.to_dict(orient="records")

            return responses_breakdown_data

        def get_df_responses_breakdown_parent_categories(
            df: pd.DataFrame,
        ) -> list[dict]:
            """
            Get df responses breakdown.

            Only parent categories.
            """

            # Count occurrence of response topics (categories)
            category_counter = Counter()
            for canonical_code in df[parent_category_col_name]:
                for c in canonical_code.split("/"):
                    category_counter[c.strip()] += 1

            responses_breakdown_data = category_counter_to_responses_breakdown_data(
                category_counter
            )

            return responses_breakdown_data

        def get_df_responses_breakdown_sub_categories(
            df: pd.DataFrame, only_sub_categories_from_parent: bool = False
        ) -> list[dict]:
            """
            Get df responses breakdown.

            Only sub-categories.
            """

            # Only get the sub-categories that belong to the parent category
            if only_sub_categories_from_parent:
                parent_category = list(self.__response_topics_unique_parent_categories)[
                    0
                ]
                df = df[(df[parent_category_col_name] == parent_category)]

            # Count occurrence of response topics (categories)
            category_counter = Counter()
            for canonical_code in df[canonical_code_col_name]:
                for c in canonical_code.split("/"):
                    category_counter[c.strip()] += 1

            responses_breakdown_data = category_counter_to_responses_breakdown_data(
                category_counter
            )

            return responses_breakdown_data

        # Responses breakdown
        if self.__campaign_code == CampaignCode.healthwellbeing:
            responses_breakdown_parent_1 = get_df_responses_breakdown_parent_categories(
                df=self.__get_df_1_copy()
            )
            responses_breakdown_parent_2 = get_df_responses_breakdown_parent_categories(
                df=self.__get_df_2_copy()
            )
            responses_breakdown_sub_1 = get_df_responses_breakdown_sub_categories(
                df=self.__get_df_1_copy()
            )
            responses_breakdown_sub_2 = get_df_responses_breakdown_sub_categories(
                df=self.__get_df_2_copy()
            )
        else:
            responses_breakdown_parent_1 = []
            responses_breakdown_parent_2 = []
            responses_breakdown_sub_1 = get_df_responses_breakdown_sub_categories(
                df=self.__get_df_1_copy()
            )
            responses_breakdown_sub_2 = get_df_responses_breakdown_sub_categories(
                df=self.__get_df_2_copy()
            )

        # responses_breakdown_parent_or_sub can contain parent categories or sub-categories
        responses_breakdown_parent_or_sub_1 = []
        responses_breakdown_parent_or_sub_2 = []
        if self.__campaign_code == CampaignCode.what_women_want_pakistan:
            if len(self.__response_topics_unique_parent_categories) == 1:
                responses_breakdown_parent_or_sub_1 = (
                    get_df_responses_breakdown_sub_categories(
                        df=self.__get_df_1_copy(),
                        only_sub_categories_from_parent=True,
                    )
                )
                responses_breakdown_parent_or_sub_2 = (
                    get_df_responses_breakdown_sub_categories(
                        df=self.__get_df_2_copy(),
                        only_sub_categories_from_parent=True,
                    )
                )
            else:
                responses_breakdown_parent_or_sub_1 = (
                    get_df_responses_breakdown_parent_categories(
                        df=self.__get_df_1_copy()
                    )
                )
                responses_breakdown_parent_or_sub_2 = (
                    get_df_responses_breakdown_parent_categories(
                        df=self.__get_df_2_copy()
                    )
                )

        # Get all unique codes from responses breakdown parent
        parent_codes_1 = [x[code_col_name] for x in responses_breakdown_parent_1]
        parent_codes_2 = [x[code_col_name] for x in responses_breakdown_parent_2]
        all_parent_codes = set(parent_codes_1 + parent_codes_2)

        # Get all unique codes from responses breakdown sub
        sub_codes_1 = [x[code_col_name] for x in responses_breakdown_sub_1]
        sub_codes_2 = [x[code_col_name] for x in responses_breakdown_sub_2]
        all_sub_codes = set(sub_codes_1 + sub_codes_2)

        # Get all unique codes from responses breakdown parent or sub
        parent_or_sub_codes_1 = [
            x[code_col_name] for x in responses_breakdown_parent_or_sub_1
        ]
        parent_or_sub_codes_2 = [
            x[code_col_name] for x in responses_breakdown_parent_or_sub_2
        ]
        all_parent_or_sub_codes = set(parent_or_sub_codes_1 + parent_or_sub_codes_2)

        def responses_breakdown_to_list(
            all_codes: set[str],
            responses_breakdown_1: list[dict],
            responses_breakdown_2: list[dict],
        ) -> list[dict]:
            """Responses breakdown to list"""

            data = []

            # For each category (code) create a dictionary with count, code and description
            for code in all_codes:
                responses_1 = [
                    x for x in responses_breakdown_1 if x[code_col_name] == code
                ]
                responses_2 = [
                    x for x in responses_breakdown_2 if x[code_col_name] == code
                ]

                # Set response
                if responses_1:
                    response_1 = responses_1[0]
                else:
                    response_1 = None
                if responses_2:
                    response_2 = responses_2[0]
                else:
                    response_2 = None

                # Set description
                description = ""
                if response_1:
                    description = response_1[description_col_name]
                if response_2:
                    description = response_2[description_col_name]

                data.append(
                    {
                        "count_1": response_1.get(count_col_name) if response_1 else 0,
                        "count_2": response_2.get(count_col_name) if response_2 else 0,
                        code_col_name.replace(f"{q_code.value}_", ""): code,
                        description_col_name.replace(
                            f"{q_code.value}_", ""
                        ): description,
                    }
                )

            return data

        # Responses breakdown
        responses_breakdown = {
            "parent_or_sub_categories": responses_breakdown_to_list(
                all_codes=all_parent_or_sub_codes,
                responses_breakdown_1=responses_breakdown_parent_or_sub_1,
                responses_breakdown_2=responses_breakdown_parent_or_sub_2,
            ),
            "parent_categories": responses_breakdown_to_list(
                all_codes=all_parent_codes,
                responses_breakdown_1=responses_breakdown_parent_1,
                responses_breakdown_2=responses_breakdown_parent_2,
            ),
            "sub_categories": responses_breakdown_to_list(
                all_codes=all_sub_codes,
                responses_breakdown_1=responses_breakdown_sub_1,
                responses_breakdown_2=responses_breakdown_sub_2,
            ),
        }

        # Sort responses breakdown parent
        responses_breakdown["parent_categories"] = sorted(
            responses_breakdown["parent_categories"],
            key=lambda x: x["count_1"],
            reverse=True,
        )

        # Sort responses breakdown sub
        responses_breakdown["sub_categories"] = sorted(
            responses_breakdown["sub_categories"],
            key=lambda x: x["count_1"],
            reverse=True,
        )

        # Sort responses breakdown parent or sub
        responses_breakdown["parent_or_sub_categories"] = sorted(
            responses_breakdown["parent_or_sub_categories"],
            key=lambda x: x["count_1"],
            reverse=True,
        )

        return responses_breakdown

    def __get_living_settings_breakdown(self) -> list[dict[str, int]]:
        """Get living setting settings breakdown"""

        df_1_copy = self.__get_df_1_copy()
        df_2_copy = self.__get_df_2_copy()

        # Get row count
        grouped_by_column_1 = df_1_copy.groupby("setting")["setting"].count()
        grouped_by_column_2 = df_2_copy.groupby("setting")["setting"].count()

        # Add count
        names = list(
            set(grouped_by_column_1.index.tolist() + grouped_by_column_2.index.tolist())
        )
        names = [name for name in names if name]

        living_settings_breakdown = []

        # Set count values
        for name in names:
            try:
                count_1 = grouped_by_column_1[name].item()
            except KeyError:
                count_1 = 0
            try:
                count_2 = grouped_by_column_2[name].item()
            except KeyError:
                count_2 = 0

            living_settings_breakdown.append(
                {
                    "name": name if helpers.contains_letters(name) else name,
                    "count_1": count_1,
                    "count_2": count_2,
                }
            )

        # Sort by count value (DESC)
        if not self.__filter_1 and not self.__filter_2:
            living_settings_breakdown = sorted(
                living_settings_breakdown,
                key=operator.itemgetter("count_1"),
                reverse=True,
            )
        elif self.__filter_1 and not self.__filter_2:
            living_settings_breakdown = sorted(
                living_settings_breakdown,
                key=operator.itemgetter("count_2"),
                reverse=True,
            )
        elif not self.__filter_1 and self.__filter_2:
            living_settings_breakdown = sorted(
                living_settings_breakdown,
                key=operator.itemgetter("count_1"),
                reverse=True,
            )

        return living_settings_breakdown

    def __get_wordcloud_words(self, q_code: QuestionCode) -> list[dict]:
        """Get wordcloud words"""

        unigram_count_dict_1 = self.__ngrams_1.get(q_code.value)
        unigram_count_dict_2 = self.__ngrams_2.get(q_code.value)

        unigram_count_dict_1 = unigram_count_dict_1[0] if unigram_count_dict_1 else ()
        unigram_count_dict_2 = unigram_count_dict_2[0] if unigram_count_dict_2 else ()

        # Get wordcloud words
        wordcloud_words = self.__get_ngram_top_words_or_phrases(
            ngram_count_dict_1=unigram_count_dict_1,
            ngram_count_dict_2=unigram_count_dict_2,
        )

        if not wordcloud_words:
            return []

        # Keep n
        n_words_to_keep = constants.n_wordcloud_words
        wordcloud_words_len = len(wordcloud_words)
        if wordcloud_words_len < n_words_to_keep:
            n_words_to_keep = wordcloud_words_len
        wordcloud_words = wordcloud_words[:n_words_to_keep]

        wordcloud_words_list = [
            {
                "text": word["word"],
                "count_1": word["count_1"],
                "count_2": word["count_2"],
            }
            for word in wordcloud_words
        ]

        return wordcloud_words_list

    def __get_top_words(self, q_code: QuestionCode) -> list[dict]:
        """Get top words"""

        unigram_count_dict_1 = self.__ngrams_1.get(q_code.value)
        unigram_count_dict_2 = self.__ngrams_2.get(q_code.value)

        unigram_count_dict_1 = unigram_count_dict_1[0] if unigram_count_dict_1 else ()
        unigram_count_dict_2 = unigram_count_dict_2[0] if unigram_count_dict_2 else ()

        # Get top words
        top_words = self.__get_ngram_top_words_or_phrases(
            ngram_count_dict_1=unigram_count_dict_1,
            ngram_count_dict_2=unigram_count_dict_2,
        )

        if not top_words:
            return []

        # Keep n
        n_words_to_keep = constants.n_top_words
        top_words_len = len(top_words)
        if top_words_len < n_words_to_keep:
            n_words_to_keep = top_words_len
        top_words = top_words[:n_words_to_keep]

        return top_words

    def __get_two_word_phrases(self, q_code: QuestionCode) -> list[dict]:
        """Get two word phrases"""

        bigram_count_dict_1 = self.__ngrams_1.get(q_code.value)
        bigram_count_dict_2 = self.__ngrams_2.get(q_code.value)

        bigram_count_dict_1 = bigram_count_dict_1[1] if bigram_count_dict_1 else {}
        bigram_count_dict_2 = bigram_count_dict_2[1] if bigram_count_dict_2 else {}

        top_words = self.__get_ngram_top_words_or_phrases(
            ngram_count_dict_1=bigram_count_dict_1,
            ngram_count_dict_2=bigram_count_dict_2,
        )

        if not top_words:
            return []

        # Keep n
        n_words_to_keep = constants.n_top_words
        top_words_len = len(top_words)
        if top_words_len < n_words_to_keep:
            n_words_to_keep = top_words_len
        top_words = top_words[:n_words_to_keep]

        return top_words

    def __get_three_word_phrases(self, q_code: QuestionCode) -> list[dict]:
        """Get three word phrases"""

        trigram_count_dict_1 = self.__ngrams_1.get(q_code.value)
        trigram_count_dict_2 = self.__ngrams_2.get(q_code.value)

        trigram_count_dict_1 = trigram_count_dict_1[2] if trigram_count_dict_1 else {}
        trigram_count_dict_2 = trigram_count_dict_2[2] if trigram_count_dict_2 else {}

        top_words = self.__get_ngram_top_words_or_phrases(
            ngram_count_dict_1=trigram_count_dict_1,
            ngram_count_dict_2=trigram_count_dict_2,
        )

        if not top_words:
            return []

        # Keep n
        n_words_to_keep = constants.n_top_words
        top_words_len = len(top_words)
        if top_words_len < n_words_to_keep:
            n_words_to_keep = top_words_len
        top_words = top_words[:n_words_to_keep]

        return top_words

    def __get_ngram_top_words_or_phrases(
        self, ngram_count_dict_1: dict, ngram_count_dict_2: dict
    ) -> list:
        """Get ngram top words/phrases"""

        if len(ngram_count_dict_1) == 0:
            return []

        unigram_count_dict_1 = sorted(
            ngram_count_dict_1.items(), key=operator.itemgetter(1)
        )
        max1 = 0

        if len(unigram_count_dict_1) > 0:
            max1 = unigram_count_dict_1[-1][1]

        # n words
        n_words = max([constants.n_wordcloud_words, constants.n_top_words])

        if len(unigram_count_dict_1) > n_words:
            unigram_count_dict_1 = unigram_count_dict_1[-n_words:]

        # words list + top words 1 frequency
        if len(unigram_count_dict_1) == 0:
            word_list, freq_list_top_1 = [], []
        else:
            word_list, freq_list_top_1 = zip(*unigram_count_dict_1)
        if (
            len(ngram_count_dict_2) > 0
            and len(unigram_count_dict_1) > 0
            and len(freq_list_top_1) > 0
        ):
            max2 = max(ngram_count_dict_2.values())
            normalisation_factor = max1 / max2
        else:
            normalisation_factor = 1

        # Top words 2 frequency
        freq_list_top_2 = [
            int(ngram_count_dict_2.get(w, 0) * normalisation_factor) for w in word_list
        ]

        top_words = [
            {
                "word": word.lower(),
                "count_1": freq_list_top_1[(len(word_list) - 1) - index],
                "count_2": freq_list_top_2[(len(word_list) - 1) - index],
            }
            for index, word in enumerate(reversed(word_list))
        ]

        return top_words

    def __get_response_topics(self) -> list[ResponseTopic]:
        """Get response topics"""

        hierarchy = self.__crud.get_category_hierarchy()
        parent_categories_descriptions = (
            self.__crud.get_parent_categories_descriptions()
        )
        response_topics = []

        for parent_category, sub_categories in hierarchy.items():
            # Add the parent category (skip if 'NA')
            if parent_category != "NA":
                # Parent category has no description
                response_topics.append(
                    ResponseTopic(
                        code=parent_category,
                        name=parent_categories_descriptions.get(
                            parent_category, parent_category
                        ),
                        is_parent=True,
                    )
                )

            # Add the sub-category
            for code, description in sub_categories.items():
                # Sub-category has description
                response_topics.append(ResponseTopic(code=code, name=description))

        return response_topics

    def __get_df_1_copy(self) -> pd.DataFrame:
        """Get dataframe 1 copy"""

        return self.__df_1.copy()

    def __get_df_2_copy(self) -> pd.DataFrame:
        """Get dataframe 2 copy"""

        return self.__df_2.copy()

    def __get_filter_description(self, filter_seq: FilterSequence) -> str:
        """Get filter description"""

        if filter_seq == "1":
            return self.__filter_1_description
        elif filter_seq == "2":
            return self.__filter_2_description
        else:
            return ""

    def __get_df_filter_description(self, df_len: int, _filter: Filter) -> str:
        """Get df filter description"""

        if not _filter:
            # Use an empty filter to generate description
            _filter = filters.get_default_filter()

        description = filters.generate_description_of_filter(
            campaign_code=self.__campaign_code,
            _filter=_filter,
            num_results=df_len,
            respondent_noun_singular=self.__crud.get_respondent_noun_singular(),
            respondent_noun_plural=self.__crud.get_respondent_noun_plural(),
        )

        return description

    def __get_filter_respondents_count(self, filter_seq: FilterSequence) -> int:
        """Get filter respondents count"""

        if filter_seq == "1":
            return len(self.__df_1.index)
        elif filter_seq == "2":
            return len(self.__df_2.index)
        else:
            return 0

    def __get_filter_average_age(self, filter_seq: FilterSequence) -> str:
        """Get filter average age"""

        average_age = "N/A"

        if filter_seq == "1":
            df_copy = self.__get_df_1_copy()
        elif filter_seq == "2":
            df_copy = self.__get_df_2_copy()
        else:
            return average_age

        # Only keep age column
        df_copy = df_copy[["age"]]

        # Age column to numeric
        df_copy["age"] = df_copy["age"].apply(
            lambda x: int(x) if isinstance(x, str) and x.isnumeric() else np.nan
        )
        df_copy = df_copy.dropna()

        # Calculate average
        if len(df_copy.index) > 0:
            average_age = df_copy["age"].mean()
            average_age = int(round(average_age))

        return str(average_age)

    def __get_filter_average_age_bucket(self, filter_seq: FilterSequence) -> str:
        """Get filter average age bucket"""

        average_age_bucket = "N/A"

        if filter_seq == "1":
            df_copy = self.__get_df_1_copy()
        elif filter_seq == "2":
            df_copy = self.__get_df_2_copy()
        else:
            return average_age_bucket

        # Only keep age_bucket column
        df_copy = df_copy[["age_bucket"]]

        if len(df_copy.index) > 0:
            average_age_bucket = " ".join(df_copy["age_bucket"].mode())
            average_age_bucket = (
                average_age_bucket
                if helpers.contains_letters(average_age_bucket)
                else average_age_bucket
            )

        return average_age_bucket

    def generate_ngrams(
        self,
        df: pd.DataFrame,
        q_code: QuestionCode,
        only_multi_word_phrases_containing_filter_term: bool = False,
        keyword: str = "",
    ) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
        """Generate ngrams"""

        # Set column name based on question code
        tokenized_column_name = q_col_names.get_tokenized_col_name(q_code=q_code)

        # Stopwords
        all_stopwords = constants.STOPWORDS
        if self.__language in all_stopwords:
            stopwords = set(all_stopwords.get(self.__language))
        else:
            stopwords = set()

        extra_stopwords = self.__crud.get_extra_stopwords()
        stopwords = stopwords.union(extra_stopwords)

        # ngram counters
        unigram_count = Counter()
        bigram_count = Counter()
        trigram_count = Counter()

        for word_list in df[tokenized_column_name]:
            # Unigram
            for i in range(len(word_list)):
                if word_list[i] not in stopwords:
                    word_single = word_list[i]
                    word_single = word_single.strip()
                    if not word_single:
                        continue
                    unigram_count[word_single] += 1

            # Bigram
            for i in range(len(word_list) - 1):
                if word_list[i] not in stopwords and word_list[i + 1] not in stopwords:
                    word_pair = f"{word_list[i]} {word_list[i + 1]}"
                    word_pair = word_pair.strip()
                    if len(word_pair.split()) < 2:
                        continue
                    bigram_count[word_pair] += 1

            # Trigram
            for i in range(len(word_list) - 2):
                if (
                    word_list[i] not in stopwords
                    and word_list[i + 1] not in stopwords
                    and word_list[i + 2] not in stopwords
                ):
                    word_trio = f"{word_list[i]} {word_list[i + 1]} {word_list[i + 2]}"
                    word_trio = word_trio.strip()
                    if len(word_trio.split()) < 3:
                        continue
                    trigram_count[word_trio] += 1

        unigram_count_dict: dict[str, int] = dict(unigram_count)
        bigram_count_dict: dict[str, int] = dict(bigram_count)
        trigram_count_dict: dict[str, int] = dict(trigram_count)

        # Only show words in bigram and trigram if it contains the keyword
        if only_multi_word_phrases_containing_filter_term and len(keyword) > 0:
            bigram_count_dict = dict(
                (a, b) for a, b in bigram_count.items() if keyword in a
            )
            trigram_count_dict = dict(
                (a, b) for a, b in trigram_count.items() if keyword in a
            )

        return unigram_count_dict, bigram_count_dict, trigram_count_dict

    def __get_ngrams_1(
        self,
        only_multi_word_phrases_containing_filter_term: bool,
        keyword: str,
        q_code: QuestionCode,
    ) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
        """Get ngrams 1"""

        # Return the cached ngrams (this is when filter 1 was not requested)
        if self.__filter_1_use_ngrams_unfiltered:
            return self.__crud.get_ngrams_unfiltered(q_code=q_code)

        (
            unigram_count_dict,
            bigram_count_dict,
            trigram_count_dict,
        ) = self.generate_ngrams(
            df=self.__get_df_1_copy(),
            only_multi_word_phrases_containing_filter_term=only_multi_word_phrases_containing_filter_term,
            keyword=keyword,
            q_code=q_code,
        )

        return unigram_count_dict, bigram_count_dict, trigram_count_dict

    def __get_ngrams_2(
        self, q_code: QuestionCode
    ) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
        """Get ngrams 2"""

        # Return the cached ngrams (this is when filter 2 was not requested)
        if self.__filter_2_use_ngrams_unfiltered:
            return self.__crud.get_ngrams_unfiltered(q_code=q_code)

        (
            unigram_count_dict,
            bigram_count_dict,
            trigram_count_dict,
        ) = self.generate_ngrams(df=self.__get_df_2_copy(), q_code=q_code)

        return unigram_count_dict, bigram_count_dict, trigram_count_dict

    def __get_histogram(self) -> dict:
        """Get histogram"""

        df_1_copy = self.__get_df_1_copy()
        df_2_copy = self.__get_df_2_copy()

        # Rename columns
        columns_rename = {
            "age": "ages",
            "age_bucket": "age_buckets",
            "age_bucket_default": "age_buckets_default",
            "gender": "genders",
            "profession": "professions",
            "canonical_country": "canonical_countries",
        }
        df_1_copy = df_1_copy.rename(columns=columns_rename)
        df_2_copy = df_2_copy.rename(columns=columns_rename)

        # Get histogram for the keys used in the dictionary below
        histogram = {
            "ages": [],
            "age_buckets": [],
            "age_buckets_default": [],
            "genders": [],
            "professions": [],
            "canonical_countries": [],
        }

        for column_name in list(histogram.keys()):
            # For each unique column value, get its row count
            grouped_by_column_1 = df_1_copy.groupby(column_name)[
                "q1_raw_response"
            ].count()
            grouped_by_column_2 = df_2_copy.groupby(column_name)[
                "q1_raw_response"
            ].count()

            # Add count for each unique column value
            names = list(
                set(
                    grouped_by_column_1.index.tolist()
                    + grouped_by_column_2.index.tolist()
                )
            )
            names = [name for name in names if name]

            # Sort age or age_bucket
            if (
                column_name == "ages"
                or column_name == "age_buckets"
                or column_name == "age_buckets_default"
            ) and len(names) > 0:
                names = sorted(
                    names,
                    key=lambda x: helpers.extract_first_occurring_numbers(
                        value=x, first_less_than_symbol_to_0=True
                    ),
                )

            # Set count values
            for name in names:
                try:
                    count_1 = grouped_by_column_1[name].item()
                except KeyError:
                    count_1 = 0
                try:
                    count_2 = grouped_by_column_2[name].item()
                except KeyError:
                    count_2 = 0

                histogram[column_name].append(
                    {
                        "name": name if helpers.contains_letters(name) else name,
                        "count_1": count_1,
                        "count_2": count_2,
                    }
                )

            # Sort the columns below by count value (ASC)
            if (
                column_name == "canonical_countries"
                or column_name == "professions"
                or column_name == "genders"
            ):
                if not self.__filter_1 and not self.__filter_2:
                    histogram[column_name] = sorted(
                        histogram[column_name], key=operator.itemgetter("count_1")
                    )
                elif self.__filter_1 and not self.__filter_2:
                    histogram[column_name] = sorted(
                        histogram[column_name], key=operator.itemgetter("count_2")
                    )
                elif not self.__filter_1 and self.__filter_2:
                    histogram[column_name] = sorted(
                        histogram[column_name], key=operator.itemgetter("count_1")
                    )

            # Limit to last 20 results
            if column_name == "canonical_countries" or column_name == "professions":
                keep_last_n = 20
                if len(histogram[column_name]) > keep_last_n:
                    histogram[column_name] = histogram[column_name][-keep_last_n:]

        return histogram

    def __get_genders_breakdown(self) -> list[dict]:
        """Get genders breakdown"""

        df_1_copy = self.__get_df_1_copy()

        gender_counts = df_1_copy["gender"].value_counts(ascending=True).to_dict()

        genders_breakdown = []
        for key, value in gender_counts.items():
            if not key:
                continue

            genders_breakdown.append({"name": key, "count": value})

        # Sort
        genders_breakdown = sorted(
            genders_breakdown, key=lambda x: x["count"], reverse=True
        )

        return genders_breakdown

    def __get_world_bubble_maps_coordinates(self) -> dict:
        """Get world bubble maps coordinates"""

        def get_country_coordinates(alpha2country_counts: dict):
            """Add coordinate and count for each country"""

            country_coordinates = []
            for key, value in alpha2country_counts.items():
                lat = constants.COUNTRY_COORDINATE.get(key)[0]
                lon = constants.COUNTRY_COORDINATE.get(key)[1]
                country_name = constants.COUNTRIES_DATA.get(key).get("name")

                if not lat or not lon or not country_name:
                    continue

                country_coordinates.append(
                    {
                        "location_code": key,
                        "location_name": country_name,
                        "n": value,
                        "lat": lat,
                        "lon": lon,
                    }
                )

            return country_coordinates

        def get_region_coordinates(region_counts: dict):
            """Add coordinate and count for each region"""

            region_coordinates = []

            for (
                alpha2country,
                canonical_country,
                region,
            ), value in region_counts.items():
                # TODO: Check empty region
                if not region:
                    coordinate_country = constants.COUNTRY_COORDINATE[alpha2country]
                    region_coordinates.append(
                        {
                            "location_code": alpha2country,
                            "location_name": canonical_country,
                            "n": value,
                            "lat": coordinate_country[0],
                            "lon": coordinate_country[1],
                        }
                    )
                    continue

                country_regions_coordinates = global_variables.region_coordinates.get(
                    alpha2country
                )

                # Check if the region's coordinate already exists
                coordinate_found = False
                if country_regions_coordinates and country_regions_coordinates.get(
                    region
                ):
                    coordinate_found = True

                # Get coordinate from googlemaps if it was not found
                if not coordinate_found:
                    coordinate = googlemaps_interactions.get_coordinate(
                        location=f"{canonical_country}, {region}"
                    )
                    if not coordinate:
                        continue

                    # Add the new coordinate
                    if not global_variables.region_coordinates.get(alpha2country):
                        global_variables.region_coordinates[alpha2country] = {}
                    global_variables.region_coordinates[alpha2country][
                        region
                    ] = coordinate

                # Create region_coordinates
                lat = global_variables.region_coordinates[alpha2country][region].get(
                    "lat"
                )
                lon = global_variables.region_coordinates[alpha2country][region].get(
                    "lon"
                )
                region_coordinates.append(
                    {
                        "location_code": region,
                        "location_name": region,
                        "n": value,
                        "lat": lat,
                        "lon": lon,
                    }
                )

            return region_coordinates

        # Get copy to not modify original
        df_1_copy = self.__get_df_1_copy()
        df_2_copy = self.__get_df_2_copy()

        # For these campaigns, use region as location
        if (
            self.__campaign_code == CampaignCode.economic_empowerment_mexico
            or self.__campaign_code == CampaignCode.what_women_want_pakistan
        ):
            # Get count of each region per country
            region_counts_1 = (
                df_1_copy[["alpha2country", "canonical_country", "region"]]
                .value_counts(ascending=True)
                .to_dict()
            )
            coordinates_1 = get_region_coordinates(region_counts=region_counts_1)

            # Get count of each region per country
            region_counts_2 = (
                df_2_copy[["alpha2country", "canonical_country", "region"]]
                .value_counts(ascending=True)
                .to_dict()
            )
            coordinates_2 = get_region_coordinates(region_counts=region_counts_2)

            coordinates = {
                "coordinates_1": coordinates_1,
                "coordinates_2": coordinates_2,
            }

        # For other campaigns, use country as location
        else:
            # Get count of each country
            alpha2country_counts_1 = (
                df_1_copy["alpha2country"].value_counts(ascending=True).to_dict()
            )
            coordinates_1 = get_country_coordinates(
                alpha2country_counts=alpha2country_counts_1
            )

            # Get count of each country
            alpha2country_counts_2 = (
                df_2_copy["alpha2country"].value_counts(ascending=True).to_dict()
            )
            coordinates_2 = get_country_coordinates(
                alpha2country_counts=alpha2country_counts_2
            )

            coordinates = {
                "coordinates_1": coordinates_1,
                "coordinates_2": coordinates_2,
            }

        return coordinates

    def __get_filters_are_identical(self) -> bool:
        """Get filters are identical"""

        return self.__filters_are_identical

    def __get_countries_list(self) -> list[Country]:
        """Get countries list"""

        countries = self.__crud.get_countries_list()

        # Sort countries
        countries = sorted(countries, key=lambda x: x.name)

        return countries

    def __get_ages(self) -> list[Age]:
        """Get ages"""

        ages = self.__crud.get_ages()

        # Sort
        ages = sorted(
            ages,
            key=lambda x: helpers.extract_first_occurring_numbers(
                value=x.code, first_less_than_symbol_to_0=True
            ),
        )

        return ages

    def __get_age_buckets(self) -> list[AgeBucket]:
        """Get age buckets"""

        age_buckets = self.__crud.get_age_buckets()

        # Remove n/a
        age_buckets = [x for x in age_buckets if x.code.lower() != "n/a"]

        # Sort
        age_buckets = sorted(
            age_buckets,
            key=lambda x: helpers.extract_first_occurring_numbers(
                value=x.code, first_less_than_symbol_to_0=True
            ),
        )

        return age_buckets

    def __get_age_buckets_default(self) -> list[AgeBucket]:
        """Get age buckets default"""

        age_buckets_default = self.__crud.get_age_buckets_default()

        # Remove n/a
        age_buckets_default = [
            x for x in age_buckets_default if x.code.lower() != "n/a"
        ]

        # Sort
        age_buckets_default = sorted(
            age_buckets_default,
            key=lambda x: helpers.extract_first_occurring_numbers(
                value=x.code, first_less_than_symbol_to_0=True
            ),
        )

        return age_buckets_default

    def __get_genders(self) -> list[Gender]:
        """Get genders"""

        genders = self.__crud.get_genders()

        return genders

    def __get_professions(self) -> list[Profession]:
        """Get professions"""

        professions = self.__crud.get_professions()

        return professions

    def __get_only_responses_from_categories_options(self) -> list[Option]:
        """Get only responses from categories options"""

        only_responses_from_categories_options = (
            self.__crud.get_only_responses_from_categories_options()
        )

        return only_responses_from_categories_options

    def __get_only_multi_word_phrases_containing_filter_term_options(
        self,
    ) -> list[Option]:
        """Get only multi-word phrases containing filter term options"""

        only_multi_word_phrases_containing_filter_term_options = (
            self.__crud.get_only_multi_word_phrases_containing_filter_term_options()
        )

        return only_multi_word_phrases_containing_filter_term_options

    def __get_list_of_ages(self, filter_seq: FilterSequence) -> list[str]:
        """Get list of ages"""

        if filter_seq == "1":
            df_copy = self.__get_df_1_copy()
        elif filter_seq == "2":
            df_copy = self.__get_df_2_copy()
        else:
            return []

        # Only keep age column
        df_copy = df_copy[["age"]]

        df_copy = df_copy["age"].dropna()

        return df_copy.tolist()

    def __get_list_of_age_buckets_default(
        self, filter_seq: FilterSequence
    ) -> list[str]:
        """Get list of age buckets"""

        if filter_seq == "1":
            df_copy = self.__get_df_1_copy()
        elif filter_seq == "2":
            df_copy = self.__get_df_2_copy()
        else:
            return []

        # Only keep age_bucket_default column
        df_copy = df_copy[["age_bucket_default"]]

        df_copy = df_copy["age_bucket_default"].dropna()

        return df_copy.tolist()

    def __get_response_years(self) -> list[str]:
        """Get response years"""

        response_years = self.__crud.get_response_years()

        return response_years
