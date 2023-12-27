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

import logging
import operator
import os
import random
from collections import Counter
from datetime import date

import numpy as np
import pandas as pd

from app import constants, utils
from app import crud
from app import global_variables
from app.core.settings import get_settings
from app.enums.legacy_campaign_code import LegacyCampaignCode
from app.helpers import category_hierarchy
from app.helpers import filters
from app.helpers import q_col_names
from app.helpers.campaigns_config_loader import CAMPAIGNS_CONFIG
from app.logginglib import init_custom_logger
from app.schemas.campaign import Campaign
from app.schemas.country import Country
from app.schemas.filter import Filter
from app.schemas.filter_options import FilterOptions
from app.schemas.option_bool import OptionBool
from app.schemas.option_str import OptionStr
from app.schemas.q_code import Question
from app.schemas.response_column import ResponseSampleColumn
from app.schemas.response_topic import ResponseTopic
from app.services import azure_blob_storage_interactions
from app.services import google_cloud_storage_interactions
from app.services import google_maps_interactions
from app.services.translator import Translator
from app.types import TFilterSequence, TCloudService

logger = logging.getLogger(__name__)
init_custom_logger(logger)

settings = get_settings()

# Cloud service
CLOUD_SERVICE: TCloudService = settings.CLOUD_SERVICE


class CampaignService:
    """
    Service for all things campaign related.
    """

    def __init__(
        self,
        campaign_code: str,
        language: str = "en",
        response_year: str = None,
        filter_1: Filter = None,
        filter_2: Filter = None,
    ):
        # Campaign code
        self.__campaign_code = campaign_code

        self.__campaign_config = CAMPAIGNS_CONFIG.get(self.__campaign_code)

        # CRUD
        self.__crud = crud.Campaign(campaign_code=self.__campaign_code)

        # Language
        self.__language = language

        # All response years
        self.__all_response_years = self.__get_response_years()

        # Response year
        self.__response_year = response_year

        # Filters
        self.__filter_1 = filter_1
        self.__filter_2 = filter_2

        # Translator
        self.__translator = Translator(cloud_service=CLOUD_SERVICE)

        # For filtering purposes, translate keyword_filter and keyword_exclude back to English
        if self.__language != "en":
            self.__translate_filter_keywords_to_en()

        # Get dataframe
        df = self.__crud.get_dataframe()

        # Filter response year
        if self.__response_year:
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
                self.__ngrams_1[q_code] = self.__get_ngrams_1(
                    only_multi_word_phrases_containing_filter_term=self.__filter_1.only_multi_word_phrases_containing_filter_term,
                    keyword=self.__filter_1.keyword_filter,
                    q_code=q_code,
                )
            else:
                self.__ngrams_1[q_code] = self.__get_ngrams_1(
                    only_multi_word_phrases_containing_filter_term=False,
                    keyword="",
                    q_code=q_code,
                )

            # Ngrams 2
            self.__ngrams_2[q_code] = self.__get_ngrams_2(q_code=q_code)

        # Check if filters are identical or not
        self.__filters_are_identical = filters.check_if_filters_are_identical(
            filter_1=filter_1, filter_2=filter_2
        )

    def get_campaign(
        self,
        q_code: str,
        include_list_of_ages: bool = False,
        include_list_of_age_buckets_default: bool = False,
    ) -> Campaign:
        """Get campaign"""

        # Included response years
        if self.__response_year:
            current_response_years = [self.__response_year]
        else:
            current_response_years = self.__all_response_years

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
        genders_breakdown = self.__get_genders_breakdown()

        # World bubble maps coordinates
        world_bubble_maps_coordinates = self.__get_world_bubble_maps_coordinates()

        # List of ages
        if include_list_of_ages and q_code == "q1":
            list_of_ages_1 = self.__get_list_of_ages(filter_seq="1")
            list_of_ages_2 = self.__get_list_of_ages(filter_seq="2")
        else:
            list_of_ages_1 = []
            list_of_ages_2 = []

        # List of age buckets
        if include_list_of_age_buckets_default and q_code == "q1":
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

        # Current question
        current_question = Question(
            code=q_code,
            question=self.__campaign_config.questions.get(q_code, ""),
        ).dict()

        # All questions
        campaign_q_codes = [x for x in self.__crud.get_q_codes()]
        all_questions = []
        for campaign_q_code in campaign_q_codes:
            if config_question := self.__campaign_config.questions.get(campaign_q_code):
                all_questions.append(
                    Question(code=campaign_q_code, question=config_question).dict()
                )
            else:
                all_questions.append(Question(code=campaign_q_code, question="").dict())
        if not all_questions:
            all_questions.append(Question(code=q_code, question="").dict())

        # Translate
        if settings.TRANSLATIONS_ENABLED and self.__language != "en":
            try:
                translator = Translator(cloud_service=CLOUD_SERVICE)
                translator.set_target_language(target_language=self.__language)

                # Extract texts
                translator.apply_t_function_campaign(
                    t=translator.extract_text,
                    campaign_code=self.__campaign_code,
                    language=self.__language,
                    current_question=current_question,
                    all_questions=all_questions,
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

                # Get translations
                translations_result = translator.apply_t_function_campaign(
                    t=translator.translate_text,
                    campaign_code=self.__campaign_code,
                    language=self.__language,
                    current_question=current_question,
                    all_questions=all_questions,
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

                # Apply translations to texts
                current_question = translations_result["current_question"]
                all_questions = translations_result["all_questions"]
                responses_sample = translations_result["responses_sample"]
                responses_breakdown = translations_result["responses_breakdown"]
                living_settings_breakdown = translations_result[
                    "living_settings_breakdown"
                ]
                top_words_and_phrases = translations_result["top_words_and_phrases"]
                histogram = translations_result["histogram"]
                genders_breakdown = translations_result["genders_breakdown"]
                world_bubble_maps_coordinates = translations_result[
                    "world_bubble_maps_coordinates"
                ]
                filter_1_average_age = translations_result["filter_1_average_age"]
                filter_2_average_age = translations_result["filter_2_average_age"]
                filter_1_description = translations_result["filter_1_description"]
                filter_2_description = translations_result["filter_2_description"]
            except (Exception,) as e:
                logger.warning(
                    f"An error occurred during translation of campaign: {str(e)}"
                )

        return Campaign(
            campaign_code=self.__campaign_code,
            current_question=current_question,
            all_questions=all_questions,
            current_response_years=current_response_years,
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
            OptionStr(value=country.alpha2_code, label=country.name).dict()
            for country in countries
        ]

        # Region options and province options
        country_region_options: list[dict[str, str | list[OptionStr]]] = []
        country_province_options: list[dict[str, str | list[OptionStr]]] = []
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
                    OptionStr(value=region.code, label=region.name).dict()
                )

                # Province
                if region.province and region.province not in provinces_found:
                    province_options["options"].append(
                        OptionStr(value=region.province, label=region.province).dict()
                    )
                    provinces_found.add(region.province)

            # Set region options
            region_options["options"] = sorted(
                region_options["options"], key=lambda x: x["label"]
            )
            country_region_options.append(region_options)

            # Set province options
            province_options["options"] = sorted(
                province_options["options"], key=lambda x: x["label"]
            )
            country_province_options.append(province_options)

        # Response topic options
        response_topics = self.__get_response_topics()
        response_topic_options = [
            OptionStr(
                value=response_topic.code,
                label=response_topic.name,
                metadata="is_parent" if response_topic.is_parent else "",
            ).dict()
            for response_topic in response_topics
        ]

        # Age options
        ages = self.__get_ages()
        age_options = [OptionStr(value=age, label=age).dict() for age in ages]

        # Age bucket options
        age_buckets = self.__get_age_buckets()
        age_bucket_options = [
            OptionStr(value=age_bucket, label=age_bucket).dict()
            for age_bucket in age_buckets
        ]

        # Age buckets default options
        age_buckets_default = self.__get_age_buckets_default()
        age_bucket_default_options = [
            OptionStr(value=age_bucket_default, label=age_bucket_default).dict()
            for age_bucket_default in age_buckets_default
        ]

        # Gender options
        genders = self.__get_genders()
        gender_options = [
            OptionStr(value=gender, label=gender).dict() for gender in genders
        ]

        # Living setting options
        living_setting_options = []
        living_settings = self.__get_living_settings()
        for index, setting in enumerate(living_settings):
            # Value & label
            value = setting
            label = setting

            # Rename label 'Prefer not to say' to 'Blank/Prefer Not To Say' at 'healthwellbeing'
            if self.__campaign_code == LegacyCampaignCode.healthwellbeing.value:
                if label and label.lower() == "prefer not to say":
                    label = "Blank/Prefer Not To Say"

            living_setting_options.append(OptionStr(value=value, label=label).dict())

        # Profession options
        professions = self.__get_professions()
        profession_options = [
            OptionStr(value=profession, label=profession).dict()
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

        # Exclude these histogram filter options
        if (
            self.__campaign_code == LegacyCampaignCode.wra03a.value
            or self.__campaign_code == LegacyCampaignCode.midwife.value
        ):
            age_options = []
        if self.__campaign_code == LegacyCampaignCode.pmn01a.value:
            age_bucket_options = []
        if self.__campaign_code == LegacyCampaignCode.midwife.value:
            gender_options = []

        # Translate
        if settings.TRANSLATIONS_ENABLED and self.__language != "en":
            try:
                translator = Translator(cloud_service=CLOUD_SERVICE)
                translator.set_target_language(target_language=self.__language)

                # Extract texts
                translator.apply_t_filter_options(
                    t=translator.extract_text,
                    country_options=country_options,
                    country_region_options=country_region_options,
                    country_province_options=country_province_options,
                    response_topic_options=response_topic_options,
                    age_options=age_options,
                    age_bucket_options=age_bucket_options,
                    age_bucket_default_options=age_bucket_default_options,
                    gender_options=gender_options,
                    living_setting_options=living_setting_options,
                    profession_options=profession_options,
                    only_responses_from_categories_options=only_responses_from_categories_options,
                    only_multi_word_phrases_containing_filter_term_options=only_multi_word_phrases_containing_filter_term_options,
                )

                # Translate extracted texts
                translator.translate_extracted_texts()

                # Get translations
                translations_result = translator.apply_t_filter_options(
                    t=translator.translate_text,
                    country_options=country_options,
                    country_region_options=country_region_options,
                    country_province_options=country_province_options,
                    response_topic_options=response_topic_options,
                    age_options=age_options,
                    age_bucket_options=age_bucket_options,
                    age_bucket_default_options=age_bucket_default_options,
                    gender_options=gender_options,
                    living_setting_options=living_setting_options,
                    profession_options=profession_options,
                    only_responses_from_categories_options=only_responses_from_categories_options,
                    only_multi_word_phrases_containing_filter_term_options=only_multi_word_phrases_containing_filter_term_options,
                )

                # Apply translations to texts
                country_options = translations_result["country_options"]
                country_region_options = translations_result["country_region_options"]
                country_province_options = translations_result[
                    "country_province_options"
                ]
                response_topic_options = translations_result["response_topic_options"]
                age_options = translations_result["age_options"]
                age_bucket_options = translations_result["age_bucket_options"]
                age_bucket_default_options = translations_result[
                    "age_bucket_default_options"
                ]
                gender_options = translations_result["gender_options"]
                living_setting_options = translations_result["living_setting_options"]
                profession_options = translations_result["profession_options"]
                only_responses_from_categories_options = translations_result[
                    "only_responses_from_categories_options"
                ]
                only_multi_word_phrases_containing_filter_term_options = (
                    translations_result[
                        "only_multi_word_phrases_containing_filter_term_options"
                    ]
                )
            except (Exception,) as e:
                logger.warning(
                    f"An error occurred during translation of filter_options: {str(e)}"
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
            living_settings=living_setting_options,
            professions=profession_options,
            only_responses_from_categories=only_responses_from_categories_options,
            only_multi_word_phrases_containing_filter_term=only_multi_word_phrases_containing_filter_term_options,
        )

    def get_histogram_options(self) -> list[dict]:
        """Get histogram options"""

        breakdown_country_option = OptionStr(
            value="breakdown-country",
            label="Show breakdown by country",
        )
        breakdown_age_option = OptionStr(
            value="breakdown-age",
            label="Show breakdown by age",
        )
        breakdown_age_bucket_option = OptionStr(
            value="breakdown-age-bucket",
            label="Show breakdown by age range",
        )
        breakdown_gender_option = OptionStr(
            value="breakdown-gender",
            label="Show breakdown by gender",
        )
        breakdown_profession_option = OptionStr(
            value="breakdown-profession",
            label="Show breakdown by profession",
        )

        if self.__campaign_code == LegacyCampaignCode.pmn01a.value:
            options = [
                breakdown_age_option.dict(),
                breakdown_gender_option.dict(),
                breakdown_profession_option.dict(),
                breakdown_country_option.dict(),
            ]
        elif (
            self.__campaign_code == LegacyCampaignCode.wra03a.value
            or self.__campaign_code == LegacyCampaignCode.midwife.value
        ):
            options = [
                breakdown_age_bucket_option.dict(),
                breakdown_gender_option.dict(),
                breakdown_profession_option.dict(),
                breakdown_country_option.dict(),
            ]
        else:
            options = [
                breakdown_age_bucket_option.dict(),
                breakdown_age_option.dict(),
                breakdown_gender_option.dict(),
                breakdown_profession_option.dict(),
                breakdown_country_option.dict(),
            ]

        # Translate
        if settings.TRANSLATIONS_ENABLED and self.__language != "en":
            try:
                translator = Translator(cloud_service=CLOUD_SERVICE)
                translator.set_target_language(target_language=self.__language)

                # Extract texts
                translator.apply_t_histogram_options(
                    translator.extract_text, options=options
                )

                # Translate extracted texts
                translator.translate_extracted_texts()

                # Get translations
                translations_result = translator.apply_t_histogram_options(
                    translator.translate_text, options=options
                )

                # Apply translations to texts
                options = translations_result["options"]
            except (Exception,) as e:
                logger.warning(
                    f"An error occurred during translation of histogram_options: {str(e)}"
                )

        return options

    def __translate_filter_keywords_to_en(self):
        """Translate keyword_filter and keyword_exclude to English"""

        if self.__filter_1 and self.__filter_1.keyword_filter:
            translated_keyword_filter_1 = self.__translator.quick_translate_text(
                text=self.__filter_1.keyword_filter,
                source_language=self.__language,
                target_language="en",
            )
            if translated_keyword_filter_1:
                self.__filter_1.keyword_filter = translated_keyword_filter_1.lower()
        if self.__filter_2 and self.__filter_2.keyword_filter:
            translated_keyword_filter_2 = self.__translator.quick_translate_text(
                text=self.__filter_2.keyword_filter,
                source_language=self.__language,
                target_language="en",
            )
            if translated_keyword_filter_2:
                self.__filter_2.keyword_filter = translated_keyword_filter_2.lower()

        if self.__filter_1 and self.__filter_1.keyword_exclude:
            translated_keyword_exclude_filter_1 = (
                self.__translator.quick_translate_text(
                    text=self.__filter_1.keyword_exclude,
                    source_language=self.__language,
                    target_language="en",
                )
            )
            if translated_keyword_exclude_filter_1:
                self.__filter_1.keyword_exclude = (
                    translated_keyword_exclude_filter_1.lower()
                )
        if self.__filter_2 and self.__filter_2.keyword_exclude:
            translated_keyword_exclude_filter_2 = (
                self.__translator.quick_translate_text(
                    text=self.__filter_2.keyword_exclude,
                    source_language=self.__language,
                    target_language="en",
                )
            )
            if translated_keyword_exclude_filter_2:
                self.__filter_2.keyword_exclude = (
                    translated_keyword_exclude_filter_2.lower()
                )

    def __get_unique_parent_categories_from_response_topics(self) -> list:
        """
        Get unique parent categories from response topics (filter_1 & filter_2)
        """

        parent_categories = set()

        mapping_code_to_parent_category = (
            category_hierarchy.get_mapping_code_to_parent_category_code(
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

        return list(parent_categories)

    def __get_responses_sample_columns(self, q_code: str) -> list[ResponseSampleColumn]:
        """Get responses sample columns"""

        responses_sample_columns = self.__crud.get_responses_sample_columns()

        # Remove description column
        if (
            self.__campaign_code == LegacyCampaignCode.healthwellbeing.value
            and q_code == "q2"
        ):
            responses_sample_columns = [
                x for x in responses_sample_columns if x.id != "description"
            ]

        return responses_sample_columns

    def __get_responses_sample(self, q_code: str) -> list[dict]:
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

    def __get_responses_sample_column_ids(self, q_code: str = None) -> list[str]:
        """Get responses sample column ids"""

        columns = self.__crud.get_responses_sample_columns()

        if not q_code:
            return [col.id for col in columns]

        # Rename column e.g. response -> q1_response
        for column in columns:
            if column.id == "response":
                column.id = f"{q_code}_response"
            if column.id == "description":
                column.id = f"{q_code}_description"

        return [col.id for col in columns]

    def __get_code_descriptions(self, code: str) -> str:
        """Get code descriptions"""

        mapping_to_description = category_hierarchy.get_mapping_code_to_description(
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

    def __get_df_responses_sample(self, df: pd.DataFrame, q_code: str) -> list[dict]:
        """Get df responses sample"""

        # Set column names based on question code
        description_col_name = q_col_names.get_description_col_name(q_code=q_code)
        canonical_code_col_name = q_col_names.get_canonical_code_col_name(q_code=q_code)
        response_col_name = q_col_names.get_response_col_name(q_code=q_code)

        # Remove rows where response is empty
        df = df[df[response_col_name] != ""]

        # Limit the sample for languages that are not English
        if self.__language == "en":
            if self.__filter_2:
                n_sample = constants.N_RESPONSES_SAMPLE // 2  # 500
            else:
                n_sample = constants.N_RESPONSES_SAMPLE  # 1000
        else:
            if self.__filter_2:
                n_sample = constants.N_RESPONSES_SAMPLE // 2 // 10  # 50
            else:
                n_sample = constants.N_RESPONSES_SAMPLE // 10  # 100

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

        # Rename columns e.g. q1_response -> response
        columns_to_rename = {x: x.replace(f"{q_code}_", "") for x in column_ids}
        df = df.rename(columns=columns_to_rename)

        responses_sample_data: list[dict] = df[columns_to_rename.values()].to_dict(
            "records"
        )

        return responses_sample_data

    def __get_responses_breakdown(self, q_code: str) -> dict[str, list]:
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

        # Get parent category if there is only one in the list
        unique_parent_categories = (
            self.__get_unique_parent_categories_from_response_topics()
        )
        only_parent_category_found = ""
        if len(unique_parent_categories) == 1:
            only_parent_category_found = unique_parent_categories[0]

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
                        "value": code,
                        "label": description,
                    }
                )

            return data

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
                    category_hierarchy.get_mapping_code_to_code(
                        campaign_code=self.__campaign_code
                    )
                )

                # Set description column
                df[description_col_name] = df[label_col_name].map(
                    category_hierarchy.get_mapping_code_to_description(
                        campaign_code=self.__campaign_code
                    )
                )

                # Drop label column
                df = df.drop([label_col_name], axis=1)

                # Drop rows with nan values
                df = df.dropna()

                # Sort the rows by count value (DESC) and keep the first n rows only
                if self.__campaign_code == LegacyCampaignCode.pmn01a.value:
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
            for parent_category in df[parent_category_col_name]:
                # Check if the parent category was already included to not include it twice
                seen_codes = set()

                for c in parent_category.split("/"):
                    if c:
                        if c not in seen_codes:
                            category_counter[c.strip()] += 1
                        seen_codes.add(c)

            responses_breakdown_data = category_counter_to_responses_breakdown_data(
                category_counter
            )

            return responses_breakdown_data

        def get_df_responses_breakdown_sub_categories(
            df: pd.DataFrame,
            include_only_sub_categories_from_parent: bool = False,
        ) -> list[dict]:
            """
            Get df responses breakdown.

            Only sub-categories.
            """

            # Only keep parent category from only_parent_category
            if include_only_sub_categories_from_parent and only_parent_category_found:
                df = df[
                    df[parent_category_col_name].str.contains(
                        r"\b" + only_parent_category_found + r"\b", regex=True
                    )
                ]

            mapping_code_to_parent_category = (
                category_hierarchy.get_mapping_code_to_parent_category_code(
                    campaign_code=self.__campaign_code
                )
            )

            # Count occurrence of response topics (categories)
            category_counter = Counter()
            for canonical_code in df[canonical_code_col_name]:
                for c in canonical_code.split("/"):
                    if c:
                        # Only count sub-categories from only_parent_category
                        if (
                            include_only_sub_categories_from_parent
                            and only_parent_category_found
                        ):
                            if (
                                mapping_code_to_parent_category.get(c.strip())
                                == only_parent_category_found
                            ):
                                category_counter[c.strip()] += 1
                        else:
                            category_counter[c.strip()] += 1

            responses_breakdown_data = category_counter_to_responses_breakdown_data(
                category_counter
            )

            return responses_breakdown_data

        # Responses breakdown
        if self.__campaign_code == LegacyCampaignCode.wwwpakistan.value:
            # If there is one unique parent category, then get its sub-categories breakdown
            if only_parent_category_found:
                responses_breakdown_parent_1 = []
                responses_breakdown_parent_2 = []
                responses_breakdown_sub_1 = get_df_responses_breakdown_sub_categories(
                    df=self.__get_df_1_copy(),
                    include_only_sub_categories_from_parent=True,
                )
                responses_breakdown_sub_2 = get_df_responses_breakdown_sub_categories(
                    df=self.__get_df_2_copy(),
                    include_only_sub_categories_from_parent=True,
                )

            # Else get the parent categories breakdown
            else:
                responses_breakdown_parent_1 = (
                    get_df_responses_breakdown_parent_categories(
                        df=self.__get_df_1_copy()
                    )
                )
                responses_breakdown_parent_2 = (
                    get_df_responses_breakdown_parent_categories(
                        df=self.__get_df_2_copy()
                    )
                )
                responses_breakdown_sub_1 = []
                responses_breakdown_sub_2 = []
        else:
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

        # Get all unique codes from responses breakdown parent
        parent_codes_1 = [x[code_col_name] for x in responses_breakdown_parent_1]
        parent_codes_2 = [x[code_col_name] for x in responses_breakdown_parent_2]
        all_parent_codes = set(parent_codes_1 + parent_codes_2)

        # Get all unique codes from responses breakdown sub
        sub_codes_1 = [x[code_col_name] for x in responses_breakdown_sub_1]
        sub_codes_2 = [x[code_col_name] for x in responses_breakdown_sub_2]
        all_sub_codes = set(sub_codes_1 + sub_codes_2)

        # Responses breakdown
        responses_breakdown = {
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
        names: list[str] = [name for name in names if name]

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

            # Value & label
            value = name
            label = name

            # Rename label 'Prefer not to say' to 'Blank/Prefer Not To Say' at 'healthwellbeing'
            if self.__campaign_code == LegacyCampaignCode.healthwellbeing.value:
                if label and label.lower() == "prefer not to say":
                    label = "Blank/Prefer Not To Say"

            living_settings_breakdown.append(
                {
                    "value": value,
                    "label": label,
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

    def __get_wordcloud_words(self, q_code: str) -> list[dict]:
        """Get wordcloud words"""

        unigram_count_dict_1 = self.__ngrams_1.get(q_code)
        unigram_count_dict_2 = self.__ngrams_2.get(q_code)

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
        n_words_to_keep = constants.N_WORDCLOUD_WORDS
        wordcloud_words_len = len(wordcloud_words)
        if wordcloud_words_len < n_words_to_keep:
            n_words_to_keep = wordcloud_words_len
        wordcloud_words = wordcloud_words[:n_words_to_keep]

        wordcloud_words_list = [
            {
                "value": word["label"],
                "text": word["label"],
                "count_1": word["count_1"],
                "count_2": word["count_2"],
            }
            for word in wordcloud_words
        ]

        return wordcloud_words_list

    def __get_top_words(self, q_code: str) -> list[dict]:
        """Get top words"""

        unigram_count_dict_1 = self.__ngrams_1.get(q_code)
        unigram_count_dict_2 = self.__ngrams_2.get(q_code)

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
        n_words_to_keep = constants.N_TOP_WORDS
        top_words_len = len(top_words)
        if top_words_len < n_words_to_keep:
            n_words_to_keep = top_words_len
        top_words = top_words[:n_words_to_keep]

        return top_words

    def __get_two_word_phrases(self, q_code: str) -> list[dict]:
        """Get two word phrases"""

        bigram_count_dict_1 = self.__ngrams_1.get(q_code)
        bigram_count_dict_2 = self.__ngrams_2.get(q_code)

        bigram_count_dict_1 = bigram_count_dict_1[1] if bigram_count_dict_1 else {}
        bigram_count_dict_2 = bigram_count_dict_2[1] if bigram_count_dict_2 else {}

        top_words = self.__get_ngram_top_words_or_phrases(
            ngram_count_dict_1=bigram_count_dict_1,
            ngram_count_dict_2=bigram_count_dict_2,
        )

        if not top_words:
            return []

        # Keep n
        n_words_to_keep = constants.N_TOP_WORDS
        top_words_len = len(top_words)
        if top_words_len < n_words_to_keep:
            n_words_to_keep = top_words_len
        top_words = top_words[:n_words_to_keep]

        return top_words

    def __get_three_word_phrases(self, q_code: str) -> list[dict]:
        """Get three word phrases"""

        trigram_count_dict_1 = self.__ngrams_1.get(q_code)
        trigram_count_dict_2 = self.__ngrams_2.get(q_code)

        trigram_count_dict_1 = trigram_count_dict_1[2] if trigram_count_dict_1 else {}
        trigram_count_dict_2 = trigram_count_dict_2[2] if trigram_count_dict_2 else {}

        top_words = self.__get_ngram_top_words_or_phrases(
            ngram_count_dict_1=trigram_count_dict_1,
            ngram_count_dict_2=trigram_count_dict_2,
        )

        if not top_words:
            return []

        # Keep n
        n_words_to_keep = constants.N_TOP_WORDS
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
        n_words = max([constants.N_WORDCLOUD_WORDS, constants.N_TOP_WORDS])

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
                "value": word.lower(),
                "label": word.lower(),
                "count_1": freq_list_top_1[(len(word_list) - 1) - index],
                "count_2": freq_list_top_2[(len(word_list) - 1) - index],
            }
            for index, word in enumerate(reversed(word_list))
        ]

        return top_words

    def __get_response_topics(self) -> list[ResponseTopic]:
        """Get response topics"""

        parent_categories = self.__crud.get_parent_categories()
        response_topics = []

        for parent_category in parent_categories:
            # Add the parent category
            if parent_category.code != "":
                # Parent category has no description
                response_topics.append(
                    ResponseTopic(
                        code=parent_category.code,
                        name=parent_category.description,
                        is_parent=True,
                    )
                )

            # Add the sub-category
            for sub_category in parent_category.sub_categories:
                # Sub-category has description
                response_topics.append(
                    ResponseTopic(code=sub_category.code, name=sub_category.description)
                )

        return response_topics

    def __get_df_1_copy(self) -> pd.DataFrame:
        """Get dataframe 1 copy"""

        return self.__df_1.copy()

    def __get_df_2_copy(self) -> pd.DataFrame:
        """Get dataframe 2 copy"""

        return self.__df_2.copy()

    def __get_filter_description(self, filter_seq: TFilterSequence) -> str:
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

    def __get_filter_respondents_count(self, filter_seq: TFilterSequence) -> int:
        """Get filter respondents count"""

        if filter_seq == "1":
            return len(self.__df_1.index)
        elif filter_seq == "2":
            return len(self.__df_2.index)
        else:
            return 0

    def __get_filter_average_age(self, filter_seq: TFilterSequence) -> str:
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

    def __get_filter_average_age_bucket(self, filter_seq: TFilterSequence) -> str:
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
                if utils.contains_letters(average_age_bucket)
                else average_age_bucket
            )

        return average_age_bucket

    def generate_ngrams(
        self,
        df: pd.DataFrame,
        q_code: str,
        only_multi_word_phrases_containing_filter_term: bool = False,
        keyword: str = "",
    ) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
        """Generate ngrams"""

        # Set column name based on question code
        lemmatized_column_name = q_col_names.get_lemmatized_col_name(q_code=q_code)

        # Stopwords
        all_stopwords = constants.STOPWORDS
        stopwords = set(all_stopwords.get("en"))
        extra_stopwords = {
            "please",
            "like",
            "want",
            "need",
            "go",
            "will",
            "-",
            ".",
            ",",
            "'",
            "&",
            "(",
            ")",
            "must",
            "should",
            "even",
            "-",
            "/",
        }
        stopwords = stopwords.union(extra_stopwords)

        # ngram counters
        unigram_count = Counter()
        bigram_count = Counter()
        trigram_count = Counter()

        for lemmatized in df[lemmatized_column_name]:
            word_list = lemmatized.split(" ")

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
        q_code: str,
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
        self, q_code: str
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
            grouped_by_column_1 = df_1_copy.groupby(column_name)["q1_response"].count()
            grouped_by_column_2 = df_2_copy.groupby(column_name)["q1_response"].count()

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
                    key=lambda x: utils.extract_first_occurring_numbers(
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
                        "value": name if utils.contains_letters(name) else name,
                        "label": name if utils.contains_letters(name) else name,
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

        # Exclude these histogram options
        if (
            self.__campaign_code == LegacyCampaignCode.wra03a.value
            or self.__campaign_code == LegacyCampaignCode.midwife.value
        ):
            if histogram.get("ages"):
                histogram["ages"] = []
        if self.__campaign_code == LegacyCampaignCode.pmn01a.value:
            if histogram.get("age_buckets"):
                histogram["age_buckets"] = []
        if self.__campaign_code == LegacyCampaignCode.midwife.value:
            if histogram.get("genders"):
                histogram["genders"] = []

        return histogram

    def __get_genders_breakdown(self) -> list[dict]:
        """Get genders breakdown"""

        df_1_copy = self.__get_df_1_copy()

        gender_counts = df_1_copy["gender"].value_counts(ascending=True).to_dict()

        genders_breakdown = []
        for key, value in gender_counts.items():
            if key:
                genders_breakdown.append({"value": key, "label": key, "count": value})

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
                # If no region was provided, use the country's coordinate
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
                    coordinate = google_maps_interactions.get_coordinate(
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
            self.__campaign_code == LegacyCampaignCode.giz.value
            or self.__campaign_code == LegacyCampaignCode.wwwpakistan.value
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

    def __get_ages(self) -> list[str]:
        """Get ages"""

        ages = self.__crud.get_ages()

        # Sort
        ages = sorted(
            ages,
            key=lambda x: utils.extract_first_occurring_numbers(
                value=x, first_less_than_symbol_to_0=True
            ),
        )

        return ages

    def __get_age_buckets(self) -> list[str]:
        """Get age buckets"""

        age_buckets = self.__crud.get_age_buckets()

        # Remove n/a
        age_buckets = [x for x in age_buckets if x.lower() != "n/a"]

        # Sort
        age_buckets = sorted(
            age_buckets,
            key=lambda x: utils.extract_first_occurring_numbers(
                value=x, first_less_than_symbol_to_0=True
            ),
        )

        return age_buckets

    def __get_age_buckets_default(self) -> list[str]:
        """Get age buckets default"""

        age_buckets_default = self.__crud.get_age_buckets_default()

        # Remove n/a
        age_buckets_default = [x for x in age_buckets_default if x.lower() != "n/a"]

        # Sort
        age_buckets_default = sorted(
            age_buckets_default,
            key=lambda x: utils.extract_first_occurring_numbers(
                value=x, first_less_than_symbol_to_0=True
            ),
        )

        return age_buckets_default

    def __get_genders(self) -> list[str]:
        """Get genders"""

        genders = self.__crud.get_genders()

        # Sort
        genders = sorted(genders, key=lambda x: x)

        return genders

    def __get_living_settings(self) -> list[str]:
        """Get living settings"""

        living_settings = self.__crud.get_living_settings()

        # Sort
        living_settings = sorted(living_settings, key=lambda x: x)

        return living_settings

    def __get_professions(self) -> list[str]:
        """Get professions"""

        professions = self.__crud.get_professions()

        # Sort
        professions = sorted(professions, key=lambda x: x)

        return professions

    def __get_only_responses_from_categories_options(self) -> list[OptionBool]:
        """Get only responses from categories options"""

        only_responses_from_categories_options = [
            OptionBool(
                value=True, label="Only show responses which match all these categories"
            ),
            OptionBool(value=False, label="Show responses in any of these categories"),
        ]

        return only_responses_from_categories_options

    def __get_only_multi_word_phrases_containing_filter_term_options(
        self,
    ) -> list[OptionBool]:
        """Get only multi-word phrases containing filter term options"""

        only_multi_word_phrases_containing_filter_term_options = [
            OptionBool(
                value=True,
                label="Only show multi-word phrases containing filter term",
            ),
            OptionBool(
                value=False,
                label="Show all multi-word phrases",
            ),
        ]

        return only_multi_word_phrases_containing_filter_term_options

    def __get_list_of_ages(self, filter_seq: TFilterSequence) -> list[str]:
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
        self, filter_seq: TFilterSequence
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

    def __get_campaign_df_export_and_filename(
        self,
        date_format: str,
        from_date: date = None,
        to_date: date = None,
        unique_filename_code: str = "",
    ):
        """Get campaign dataframe for exporting and filename"""

        # Dataframe
        df = self.__get_df_1_copy()

        # Drop columns
        df = df.drop(
            columns=[
                "age_bucket_default",
                "data_source",
            ],
            errors="ignore",
        )

        # CSV filename
        if unique_filename_code:
            unique_filename_code = f"_{unique_filename_code}"
        csv_filename = f"export_{self.__campaign_code}{unique_filename_code}.csv"

        # Filter by date
        if from_date and to_date:
            df = df[
                (df["ingestion_time"].dt.date >= from_date)
                & (df["ingestion_time"].dt.date <= to_date)
            ]
            csv_filename_without_ext = csv_filename.replace(".csv", "")
            csv_filename = f"{csv_filename_without_ext}_{from_date.strftime(date_format)}_to_{to_date.strftime(date_format)}.csv"

        # Convert date to string
        df["ingestion_time"] = df["ingestion_time"].apply(
            lambda x: x.strftime(date_format) if x and not isinstance(x, str) else ""
        )

        return df, csv_filename

    def get_campaign_data_url_and_filename(
        self,
        cloud_service: TCloudService,
        from_date: date = None,
        to_date: date = None,
        unique_filename_code: str = "",
    ) -> tuple[str, str]:
        """
        Get campaign data url and filename

        :param cloud_service: Cloud service
        :param from_date: From Date
        :param to_date: to date
        :param unique_filename_code: Code to attach to filename uploaded to Cloud Storage.
        This code is unique per campaign_code and filters so that requesting the same filters does not have to create a new CSV file, but the existing file will be used.
        """

        def remove_unique_filename_code(_csv_filename: str, _unique_filename_code):
            """
            Function used after the file has been uploaded to cloud Storage.
            Remove the filename code because the user should not see it in the filename.
            """

            _csv_filename = _csv_filename.replace(f"_{_unique_filename_code}", "")

            return _csv_filename

        # Date format
        date_format = "%Y_%m_%d"

        # Get df and filename
        df, csv_filename = self.__get_campaign_df_export_and_filename(
            date_format=date_format,
            from_date=from_date,
            to_date=to_date,
            unique_filename_code=unique_filename_code,
        )

        # Google
        if cloud_service == "google":
            # File paths
            csv_filepath = f"/tmp/{csv_filename}"
            creating_csv_filepath = f"/tmp/wra_creating_{csv_filename}"
            storage_csv_filepath = f"{csv_filename}"
            bucket_name = settings.GOOGLE_CLOUD_STORAGE_BUCKET_TMP_DATA

            # If file exists in Google Cloud Storage
            if google_cloud_storage_interactions.blob_exists(
                bucket_name=bucket_name,
                blob_name=storage_csv_filepath,
            ):
                # Get url
                url = google_cloud_storage_interactions.get_blob_url(
                    bucket_name=bucket_name,
                    blob_ame=storage_csv_filepath,
                )

                # Remove unique filename code
                if unique_filename_code:
                    csv_filename = remove_unique_filename_code(
                        _csv_filename=csv_filename,
                        _unique_filename_code=unique_filename_code,
                    )

                return url, csv_filename

            # If file does not exist in Google Cloud Storage
            else:
                if not os.path.isfile(csv_filepath):
                    # Cleanup
                    if os.path.isfile(creating_csv_filepath):
                        os.remove(creating_csv_filepath)

                    # Save dataframe to csv file
                    df.to_csv(
                        path_or_buf=creating_csv_filepath, index=False, header=True
                    )

                    # Rename
                    os.rename(src=creating_csv_filepath, dst=csv_filepath)

                # Upload
                google_cloud_storage_interactions.upload_file(
                    bucket_name=bucket_name,
                    source_filename=csv_filepath,
                    destination_filename=storage_csv_filepath,
                )

                # Remove from tmp
                os.remove(csv_filepath)

                # Get url
                url = google_cloud_storage_interactions.get_blob_url(
                    bucket_name=bucket_name,
                    blob_ame=storage_csv_filepath,
                )

                # Remove unique filename code
                if unique_filename_code:
                    csv_filename = remove_unique_filename_code(
                        _csv_filename=csv_filename,
                        _unique_filename_code=unique_filename_code,
                    )

                return url, csv_filename

        # Azure
        elif cloud_service == "azure":
            container_name: str = settings.AZURE_STORAGE_CONTAINER_TMP_DATA

            # If file exists in Azure Blob Storage
            if azure_blob_storage_interactions.blob_exists(
                container_name=container_name, blob_name=csv_filename
            ):
                # Get url
                url = azure_blob_storage_interactions.get_blob_url(
                    container_name=container_name, blob_name=csv_filename
                )

                # Remove unique filename code
                if unique_filename_code:
                    csv_filename = remove_unique_filename_code(
                        _csv_filename=csv_filename,
                        _unique_filename_code=unique_filename_code,
                    )

                return url, csv_filename

            # If file does not exist in Azure Blob Storage
            else:
                # Upload
                azure_blob_storage_interactions.upload_df_as_csv(
                    container_name=container_name,
                    df=df,
                    csv_filename=csv_filename,
                )

                # Get url
                url = azure_blob_storage_interactions.get_blob_url(
                    container_name=container_name, blob_name=csv_filename
                )

                # Remove unique filename code
                if unique_filename_code:
                    csv_filename = remove_unique_filename_code(
                        _csv_filename=csv_filename,
                        _unique_filename_code=unique_filename_code,
                    )

                return url, csv_filename
