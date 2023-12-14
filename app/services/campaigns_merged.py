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

import pandas as pd

from app import utils, constants
from app.enums.legacy_campaign_code import LegacyCampaignCode
from app.helpers import filters
from app.schemas.campaign import Campaign
from app.schemas.filter import Filter
from app.schemas.filter_options import FilterOptions
from app.schemas.q_code import Question
from app.services.translator import Translator
from app.types import FilterSequence


class CampaignsMergedService:
    def __init__(
        self,
        language: str,
        campaigns_data: dict[str, list[Campaign]] = None,
        campaigns_filter_options: list[dict] = None,
        campaigns_histogram_options: list[list[dict]] = None,
        filter_1: Filter | None = None,
        filter_2: Filter | None = None,
    ):
        self.__language = language

        if campaigns_data:
            self.__campaigns_data = campaigns_data
        else:
            self.__campaigns_data: dict[str, list[Campaign]] = {}

        if campaigns_filter_options:
            self.__campaigns_filter_options = campaigns_filter_options
        else:
            self.__campaigns_filter_options: list[dict] = []

        if campaigns_histogram_options:
            self.__campaigns_histogram_options = campaigns_histogram_options
        else:
            self.__campaigns_histogram_options: list[list[dict]] = []

        # Campaigns data list for question code 1 only
        self.__campaigns_data_q1 = [x[0] for x in self.__campaigns_data.values() if x]

        # Campaigns data list (flattened) for all question codes
        self.__campaigns_data_all_q = [
            x
            for sub_list in [x for x in self.__campaigns_data.values()]
            for x in sub_list
        ]

        # Check if filters are identical or not
        self.__filters_are_identical = filters.check_if_filters_are_identical(
            filter_1=filter_1, filter_2=filter_2
        )

    def get_campaign(self):
        """Get campaign"""

        # Responses sample
        responses_sample = self.__get_responses_sample()

        # Responses breakdown
        responses_breakdown = self.__get_responses_breakdown()

        # Top words or phrases
        top_words_and_phrases = self.__get_top_words_and_phrases()

        # Histogram
        histogram = self.__get_histogram()

        # World bubble maps coordinates
        world_bubble_maps_coordinates = self.__get_world_bubble_maps_coordinates()

        # Filter respondents count
        filter_1_respondents_count = self.__get_filter_respondents_count(filter_seq="1")
        filter_2_respondents_count = self.__get_filter_respondents_count(filter_seq="2")

        # Average age
        filter_1_average_age = (
            "N/A"  # Not all campaigns contain ages, only use age buckets below
        )
        filter_2_average_age = (
            "N/A"  # Not all campaigns contain ages, only use age buckets below
        )
        filter_1_average_age_bucket = self.__get_filter_average_age_bucket(
            filter_seq="1"
        )
        filter_2_average_age_bucket = self.__get_filter_average_age_bucket(
            filter_seq="2"
        )

        # Filter description
        filter_1_description = self.__get_filter_description(filter_seq="1")
        filter_2_description = self.__get_filter_description(filter_seq="2")

        # Filters are identical
        filters_are_identical = self.__get_filters_are_identical()

        return Campaign(
            campaign_code="",
            current_response_years=[],
            all_response_years=[],
            current_question=Question(code="", question="").dict(),
            all_questions=[],
            responses_sample=responses_sample,
            responses_breakdown=responses_breakdown,
            living_settings_breakdown=[],
            top_words_and_phrases=top_words_and_phrases,
            histogram=histogram,
            genders_breakdown=[],
            world_bubble_maps_coordinates=world_bubble_maps_coordinates,
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
        country_options = self.__get_country_options()

        # Country regions options
        country_regions_options = self.__get_country_regions_options()

        # Response topic options
        response_topics_options = self.__get_response_topics_options()

        # Age options
        age_options = []

        # Age bucket options
        age_bucket_options = self.__get_age_bucket_options()

        # Only responses from categories options
        only_responses_from_categories_options = (
            self.__get_only_responses_from_categories_options()
        )

        # Only multi-word phrases containing filter term
        only_multi_word_phrases_containing_filter_term_options = (
            self.__get_only_multi_word_phrases_containing_filter_term_options()
        )

        return FilterOptions(
            countries=country_options,
            country_regions=country_regions_options,
            response_topics=response_topics_options,
            ages=age_options,
            age_buckets=age_bucket_options,
            genders=[],
            professions=[],
            only_responses_from_categories=only_responses_from_categories_options,
            only_multi_word_phrases_containing_filter_term=only_multi_word_phrases_containing_filter_term_options,
        )

    def get_histogram_options(self) -> list[dict]:
        """Get histogram options"""

        histogram_options = utils.get_unique_flattened_list_of_dictionaries(
            data_lists=self.__campaigns_histogram_options
        )

        # Only keep country breakdown and age bucket breakdown option
        histogram_options = [
            x
            for x in histogram_options
            if x.get("value") == "breakdown-country"
            or x.get("value") == "breakdown-age-bucket"
        ]

        return histogram_options

    def __get_responses_sample(self) -> dict[str, list[dict] | list]:
        """Get responses sample"""

        responses_sample = {
            "columns": utils.get_unique_flattened_list_of_dictionaries(
                data_lists=[
                    x.responses_sample.get("columns")
                    for x in self.__campaigns_data_all_q
                    if x.responses_sample
                ],
            ),
            "data": utils.get_distributed_list_of_dictionaries(
                data_lists=[
                    x.responses_sample.get("data")
                    for x in self.__campaigns_data_all_q
                    if x.responses_sample
                ],
                n_items=1000,
                shuffle=True,
            ),
        }

        # Responses sample - Only keep these columns
        columns_to_keep = {"response", "description", "canonical_country", "age"}
        responses_sample["columns"] = [
            x for x in responses_sample["columns"] if x.get("id") in columns_to_keep
        ]

        return responses_sample

    def __get_responses_breakdown(self) -> dict[str, list]:
        """Get responses breakdown"""

        # Response breakdown
        responses_breakdown = {
            "parent_categories": [],  # Ignore, not all campaigns contain parent_categories
            "sub_categories": utils.get_merged_flattened_list_of_dictionaries(
                data_lists=[
                    x.responses_breakdown["sub_categories"]
                    for x in self.__campaigns_data_all_q
                    if x.responses_breakdown
                ],
                unique_key="value",
                keys_to_merge=["count_1", "count_2"],
            ),
            "parent_or_sub_categories": [],  # Ignore, not all campaigns contain parent_or_sub_categories
        }

        # Responses breakdown (sorted)
        responses_breakdown["sub_categories"] = sorted(
            responses_breakdown["sub_categories"],
            key=lambda d: d.get("count_1"),
            reverse=True,
        )

        return responses_breakdown

    def __get_top_words_and_phrases(self) -> dict[str, list[dict]]:
        """Get top words and phrases"""

        # Get wordcloud words
        wordcloud_words = utils.get_merged_flattened_list_of_dictionaries(
            data_lists=[
                x.top_words_and_phrases.get("wordcloud_words")
                for x in self.__campaigns_data_all_q
                if x.top_words_and_phrases
            ],
            unique_key="text",
            keys_to_merge=["count_1"],
        )

        # Get top words (use data from wordcloud words)
        top_words = [
            {"label": x["text"], "count_1": x["count_1"], "count_2": x["count_2"]}
            for x in wordcloud_words
        ][: constants.N_TOP_WORDS]

        # Two word phrases
        two_word_phrases = utils.get_merged_flattened_list_of_dictionaries(
            data_lists=[
                x.top_words_and_phrases.get("two_word_phrases")
                for x in self.__campaigns_data_all_q
                if x.top_words_and_phrases
            ],
            unique_key="label",
            keys_to_merge=["count_1", "count_2"],
        )

        # Three word phrases
        three_word_phrases = utils.get_merged_flattened_list_of_dictionaries(
            data_lists=[
                x.top_words_and_phrases.get("three_word_phrases")
                for x in self.__campaigns_data_all_q
                if x.top_words_and_phrases
            ],
            unique_key="label",
            keys_to_merge=["count_1", "count_2"],
        )

        # Top words or phrases
        top_words_and_phrases = {
            "top_words": top_words,
            "two_word_phrases": two_word_phrases,
            "three_word_phrases": three_word_phrases,
            "wordcloud_words": wordcloud_words,
        }

        # Top words or phrases (sorted)
        top_words_and_phrases["top_words"] = sorted(
            top_words_and_phrases["top_words"],
            key=lambda d: d.get("count_1"),
            reverse=True,
        )
        top_words_and_phrases["two_word_phrases"] = sorted(
            top_words_and_phrases["two_word_phrases"],
            key=lambda d: d.get("count_1"),
            reverse=True,
        )
        top_words_and_phrases["three_word_phrases"] = sorted(
            top_words_and_phrases["three_word_phrases"],
            key=lambda d: d.get("count_1"),
            reverse=True,
        )
        top_words_and_phrases["wordcloud_words"] = sorted(
            top_words_and_phrases["wordcloud_words"],
            key=lambda d: d.get("count_1"),
            reverse=True,
        )

        # Top words or phrases (check list size)
        n_top_words = 20
        if len(top_words_and_phrases["top_words"]) > n_top_words:
            top_words_and_phrases["top_words"] = top_words_and_phrases["top_words"][
                :n_top_words
            ]
        if len(top_words_and_phrases["two_word_phrases"]) > n_top_words:
            top_words_and_phrases["two_word_phrases"] = top_words_and_phrases[
                "two_word_phrases"
            ][:n_top_words]
        if len(top_words_and_phrases["three_word_phrases"]) > n_top_words:
            top_words_and_phrases["three_word_phrases"] = top_words_and_phrases[
                "three_word_phrases"
            ][:n_top_words]
        if len(top_words_and_phrases["wordcloud_words"]) > constants.N_WORDCLOUD_WORDS:
            top_words_and_phrases["wordcloud_words"] = top_words_and_phrases[
                "wordcloud_words"
            ][: constants.N_WORDCLOUD_WORDS]

        return top_words_and_phrases

    def __get_living_settings_breakdown(self) -> list:
        """Get living settings breakdown"""

        return []

    def __get_histogram(self) -> dict[str, list | list[dict]]:
        """Get histogram"""

        histogram = {
            "ages": [],
            "age_buckets": [],
            "age_buckets_default": utils.get_merged_flattened_list_of_dictionaries(
                data_lists=[
                    x.histogram.get("age_buckets_default")
                    for x in self.__campaigns_data_q1
                    if x.histogram
                ],
                unique_key="label",
                keys_to_merge=["count_1", "count_2"],
            ),
            "genders": [],
            "professions": [],
            "canonical_countries": utils.get_merged_flattened_list_of_dictionaries(
                data_lists=[
                    x.histogram.get("canonical_countries")
                    for x in self.__campaigns_data_q1
                    if x.histogram
                ],
                unique_key="label",
                keys_to_merge=["count_1", "count_2"],
            ),
        }

        # sort countries
        histogram["canonical_countries"] = sorted(
            histogram["canonical_countries"],
            key=lambda x: x.get("count_1"),
            reverse=True,
        )

        # Sort age buckets default
        histogram["age_buckets_default"] = sorted(
            histogram["age_buckets_default"],
            key=lambda x: utils.extract_first_occurring_numbers(
                value=x.get("label"), first_less_than_symbol_to_0=True
            ),
        )

        return histogram

    def __get_genders_breakdown(self) -> list:
        """Get genders breakdown"""

        return []

    def __get_world_bubble_maps_coordinates(self) -> dict[str, list[dict]]:
        """Get world bubble maps coordinates"""

        # Translator
        translator = Translator(cloud_service="google")
        translator.set_target_language(target_language=self.__language)

        # Change the coordinate from region to the country's coordinate
        for campaign_data in self.__campaigns_data_q1:
            if campaign_data.campaign_code == LegacyCampaignCode.wwwpakistan.value:
                coordinate_pk = constants.COUNTRY_COORDINATE["PK"]
                for coordinate in (
                    campaign_data.world_bubble_maps_coordinates["coordinates_1"]
                    + campaign_data.world_bubble_maps_coordinates["coordinates_2"]
                ):
                    coordinate["location_code"] = "PK"
                    coordinate["location_name"] = translator.translate_text("Pakistan")
                    coordinate["lat"] = coordinate_pk[0]
                    coordinate["lon"] = coordinate_pk[1]

        # Change the coordinate from region to the country's coordinate
        for campaign_data in self.__campaigns_data_q1:
            if campaign_data.campaign_code == LegacyCampaignCode.giz.value:
                coordinate_mx = constants.COUNTRY_COORDINATE["MX"]
                for coordinate in (
                    campaign_data.world_bubble_maps_coordinates["coordinates_1"]
                    + campaign_data.world_bubble_maps_coordinates["coordinates_2"]
                ):
                    coordinate["location_code"] = "MX"
                    coordinate["location_name"] = translator.translate_text("Mexico")
                    coordinate["lat"] = coordinate_mx[0]
                    coordinate["lon"] = coordinate_mx[1]

        # Coordinates
        world_bubble_maps_coordinates = {
            "coordinates_1": utils.get_merged_flattened_list_of_dictionaries(
                data_lists=[
                    x.world_bubble_maps_coordinates.get("coordinates_1")
                    for x in self.__campaigns_data_q1
                    if x.world_bubble_maps_coordinates
                ],
                unique_key="location_code",
                keys_to_merge=["n"],
            ),
            "coordinates_2": utils.get_merged_flattened_list_of_dictionaries(
                data_lists=[
                    x.world_bubble_maps_coordinates.get("coordinates_2")
                    for x in self.__campaigns_data_q1
                    if x.world_bubble_maps_coordinates
                ],
                unique_key="location_code",
                keys_to_merge=["n"],
            ),
        }

        return world_bubble_maps_coordinates

    def __get_filter_respondents_count(self, filter_seq: FilterSequence) -> int:
        """Get filter respondents count"""

        if filter_seq == "1":
            filter_respondents_counts: list[int] = [
                x.filter_1_respondents_count for x in self.__campaigns_data_q1
            ]
        elif filter_seq == "2":
            filter_respondents_counts: list[int] = [
                x.filter_2_respondents_count for x in self.__campaigns_data_q1
            ]
        else:
            filter_respondents_counts = []

        if not filter_respondents_counts:
            filter_respondents_counts = [0]

        return sum(filter_respondents_counts)

    def __get_filter_average_age(self, filter_seq: FilterSequence) -> str:
        """Get filter average age"""

        average_age = "N/A"

        # Create a list containing all ages
        list_of_all_ages: list[int] = []
        for campaign_data in self.__campaigns_data_q1:
            if filter_seq == "1":
                campaign_data_list_of_ages = [
                    int(x) for x in campaign_data.list_of_ages_1 if x.isnumeric()
                ]
            elif filter_seq == "2":
                campaign_data_list_of_ages = [
                    int(x) for x in campaign_data.list_of_ages_2 if x.isnumeric()
                ]
            else:
                campaign_data_list_of_ages = []

            list_of_all_ages.extend(campaign_data_list_of_ages)

        # Calculate average
        if len(list_of_all_ages) > 0:
            df = pd.DataFrame(data=list_of_all_ages, columns=["age"])
            average_age = int(round(df["age"].mean(numeric_only=True)))

        return str(average_age)

    def __get_filter_average_age_bucket(self, filter_seq: FilterSequence) -> str:
        """Get filter average age bucket"""

        # Create a list containing all age buckets
        list_of_all_age_buckets: list[str] = []
        for campaign_data in self.__campaigns_data_q1:
            if filter_seq == "1":
                campaign_data_list_of_age_buckets = campaign_data.list_of_age_buckets_1
            elif filter_seq == "2":
                campaign_data_list_of_age_buckets = campaign_data.list_of_age_buckets_2
            else:
                campaign_data_list_of_age_buckets = []

            list_of_all_age_buckets.extend(campaign_data_list_of_age_buckets)

        # Calculate average age bucket
        df = pd.DataFrame(list_of_all_age_buckets, columns=["age_bucket"])
        average_age = "N/A"
        if len(df.index) > 0:
            average_age = " ".join(df["age_bucket"].mode())

        return average_age

    def __get_filters_are_identical(self) -> bool:
        """Get filters are identical"""

        return self.__filters_are_identical

    def __get_filter_description(self, filter_seq: FilterSequence) -> str:
        """
        Get filter description.

        Use filter description from 'what_young_people_want' as this campaign uses respondent_noun as respondent.
        """

        for campaign in self.__campaigns_data_q1:
            if campaign.campaign_code == LegacyCampaignCode.pmn01a.value:
                if filter_seq == "1":
                    return campaign.filter_1_description
                if filter_seq == "2":
                    return campaign.filter_2_description

        return ""

    def __get_country_options(self) -> list[dict]:
        """Get country options"""

        country_options = utils.get_unique_flattened_list_of_dictionaries(
            data_lists=[
                [y for y in x.get("countries") or []]
                for x in self.__campaigns_filter_options
            ]
        )

        # Sort
        country_options = sorted(country_options, key=lambda x: x["label"])

        return country_options

    def __get_country_regions_options(self) -> list[dict]:
        """Get country regions options"""

        country_regions_options = utils.get_unique_flattened_list_of_dictionaries(
            data_lists=[
                [y for y in x.get("country_regions") or []]
                for x in self.__campaigns_filter_options
            ]
        )

        # Sort
        country_regions_options = sorted(
            country_regions_options, key=lambda x: x["country_alpha2_code"]
        )

        return country_regions_options

    def __get_response_topics_options(self) -> list[dict]:
        """Get response topic options"""

        response_topics_options = utils.get_unique_flattened_list_of_dictionaries(
            data_lists=[
                [y for y in x.get("response_topics") or []]
                for x in self.__campaigns_filter_options
            ]
        )

        # Remove metadata
        for option in response_topics_options:
            if option.get("metadata"):
                option["metadata"] = ""

        return response_topics_options

    def __get_age_options(self) -> list[dict]:
        """Get age options"""

        age_options = utils.get_unique_flattened_list_of_dictionaries(
            data_lists=[
                [y for y in x.get("age") or []] for x in self.__campaigns_filter_options
            ]
        )

        # Sort age options
        age_options = sorted(
            age_options,
            key=lambda x: utils.extract_first_occurring_numbers(
                value=x.get("label"), first_less_than_symbol_to_0=True
            ),
        )

        return age_options

    def __get_age_bucket_options(self) -> list[dict]:
        """Get age bucket options"""

        age_bucket_options = utils.get_unique_flattened_list_of_dictionaries(
            data_lists=[
                [y for y in x.get("age_buckets_default") or []]
                for x in self.__campaigns_filter_options
            ]
        )

        # Sort age bucket options
        age_bucket_options = sorted(
            age_bucket_options,
            key=lambda x: utils.extract_first_occurring_numbers(
                value=x.get("label"), first_less_than_symbol_to_0=True
            ),
        )

        return age_bucket_options

    def __get_only_responses_from_categories_options(self) -> list[dict]:
        """Get only responses from categories options"""

        return self.__campaigns_filter_options[0].get("only_responses_from_categories")

    def __get_only_multi_word_phrases_containing_filter_term_options(
        self,
    ) -> list[dict]:
        """Get only multi-word phrases containing filter term options"""

        return self.__campaigns_filter_options[0].get(
            "only_multi_word_phrases_containing_filter_term"
        )
