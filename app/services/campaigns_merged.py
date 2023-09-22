"""
Handles processing of data and business logic for campaigns merged
"""

import pandas as pd

from app import helpers, constants
from app.enums.campaign_code import CampaignCode
from app.schemas.campaign import Campaign
from app.schemas.filter import Filter
from app.schemas.filter_options import FilterOptions
from app.types import FilterSequence
from app.utils import filters


class CampaignsMergedService:
    def __init__(
        self,
        campaigns_data: dict[str, list[Campaign]] = None,
        campaigns_filter_options: list[dict] = None,
        campaigns_who_the_people_are_options: list[list[dict]] = None,
        filter_1: Filter | None = None,
        filter_2: Filter | None = None,
    ):
        if campaigns_data:
            self.__campaigns_data = campaigns_data
        else:
            self.__campaigns_data: dict[str, list[Campaign]] = {}

        if campaigns_filter_options:
            self.__campaigns_filter_options = campaigns_filter_options
        else:
            self.__campaigns_filter_options: list[dict] = []

        if campaigns_who_the_people_are_options:
            self.__campaigns_who_the_people_are_options = (
                campaigns_who_the_people_are_options
            )
        else:
            self.__campaigns_who_the_people_are_options: list[list[dict]] = []

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

        # Living settings breakdown
        # living_settings_breakdown = self.__get_living_settings_breakdown()

        # Top words or phrases
        top_words_and_phrases = self.__get_top_words_and_phrases()

        # Histogram
        histogram = self.__get_histogram()

        # Genders breakdown
        # genders_breakdown = self.__get_genders_breakdown()

        # World bubble maps coordinates
        world_bubble_maps_coordinates = self.__get_world_bubble_maps_coordinates()

        # Filter 1 respondents count
        filter_1_respondents_count = self.__get_filter_respondents_count(filter_seq="1")

        # Filter 2 respondents count
        filter_2_respondents_count = self.__get_filter_respondents_count(filter_seq="2")

        # Filter 1 average age
        filter_1_average_age = self.__get_filter_average_age(filter_seq="1")

        # Filter 2 average age
        filter_2_average_age = self.__get_filter_average_age(filter_seq="2")

        # Filter 1 description
        filter_1_description = self.__get_filter_description(filter_seq="1")

        # Filter 2 description
        filter_2_description = self.__get_filter_description(filter_seq="2")

        # Filters are identical
        filters_are_identical = self.__get_filters_are_identical()

        return Campaign(
            campaign_code="",
            q_code="",
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

        # Ages
        ages = []

        # Age ranges
        age_ranges = self.__get_age_ranges_options()

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
            ages=ages,
            age_ranges=age_ranges,
            genders=[],
            professions=[],
            only_responses_from_categories=only_responses_from_categories_options,
            only_multi_word_phrases_containing_filter_term=only_multi_word_phrases_containing_filter_term_options,
        )

    def get_who_the_people_are_options(self) -> list[dict]:
        """Get who the people are options"""

        who_the_people_are_options = helpers.get_unique_flattened_list_of_dictionaries(
            data_lists=self.__campaigns_who_the_people_are_options
        )

        # Only keep country breakdown option
        who_the_people_are_options = [
            x
            for x in who_the_people_are_options
            if x.get("value") == "breakdown-country"
        ]

        return who_the_people_are_options

    def __get_responses_sample(self) -> dict[str, list[dict] | list]:
        """Get responses sample"""

        responses_sample = {
            "columns": helpers.get_unique_flattened_list_of_dictionaries(
                data_lists=[
                    x.responses_sample.get("columns")
                    for x in self.__campaigns_data_all_q
                    if x.responses_sample
                ],
            ),
            "data": helpers.get_distributed_list_of_dictionaries(
                data_lists=[
                    x.responses_sample.get("data")
                    for x in self.__campaigns_data_all_q
                    if x.responses_sample
                ],
                n_items=1000,
                shuffle=True,
            ),
        }

        # Responses sample - (keep only columns raw_response, description, canonical_country and age)
        columns_to_keep = {"raw_response", "description", "canonical_country", "age"}
        responses_sample["columns"] = [
            x for x in responses_sample["columns"] if x.get("id") in columns_to_keep
        ]

        return responses_sample

    def __get_responses_breakdown(self) -> list[dict]:
        """Get responses breakdown"""

        responses_breakdown = helpers.get_merged_flattened_list_of_dictionaries(
            data_lists=[
                x.responses_breakdown
                for x in self.__campaigns_data_all_q
                if x.responses_breakdown
            ],
            by_key="code",
            keys_to_merge=["count_1", "count_2"],
        )

        # Responses breakdown (sorted)
        responses_breakdown = sorted(
            responses_breakdown, key=lambda d: d.get("count_1"), reverse=True
        )

        return responses_breakdown

    def __get_top_words_and_phrases(self) -> dict[str, list[dict]]:
        """Get top words and phrases"""

        # Get wordcloud words
        wordcloud_words = helpers.get_merged_flattened_list_of_dictionaries(
            data_lists=[
                x.top_words_and_phrases.get("wordcloud_words")
                for x in self.__campaigns_data_all_q
                if x.top_words_and_phrases
            ],
            by_key="text",
            keys_to_merge=["count_1"],
        )

        # Get top words (use data from wordcloud words)
        top_words = [
            {"word": x["text"], "count_1": x["count_1"], "count_2": x["count_2"]}
            for x in wordcloud_words
        ][: constants.n_top_words]

        # Two word phrases
        two_word_phrases = helpers.get_merged_flattened_list_of_dictionaries(
            data_lists=[
                x.top_words_and_phrases.get("two_word_phrases")
                for x in self.__campaigns_data_all_q
                if x.top_words_and_phrases
            ],
            by_key="word",
            keys_to_merge=["count_1", "count_2"],
        )

        # Three word phrases
        three_word_phrases = helpers.get_merged_flattened_list_of_dictionaries(
            data_lists=[
                x.top_words_and_phrases.get("three_word_phrases")
                for x in self.__campaigns_data_all_q
                if x.top_words_and_phrases
            ],
            by_key="word",
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
        if len(top_words_and_phrases["wordcloud_words"]) > constants.n_wordcloud_words:
            top_words_and_phrases["wordcloud_words"] = top_words_and_phrases[
                "wordcloud_words"
            ][: constants.n_wordcloud_words]

        return top_words_and_phrases

    def __get_living_settings_breakdown(self) -> list:
        """Get living settings breakdown"""

        return []

    def __get_histogram(self) -> dict[str, list | list[dict]]:
        """Get histogram"""

        histogram = {
            "ages": [],
            "age_ranges": [],
            "genders": [],
            "professions": [],
            "canonical_countries": helpers.get_merged_flattened_list_of_dictionaries(
                data_lists=[
                    x.histogram.get("canonical_countries")
                    for x in self.__campaigns_data_q1
                    if x.histogram
                ],
                by_key="name",
                keys_to_merge=["count_1", "count_2"],
            ),
        }

        histogram["canonical_countries"] = sorted(
            histogram["canonical_countries"],
            key=lambda d: d.get("count_1"),
            reverse=True,
        )

        return histogram

    def __get_genders_breakdown(self) -> list:
        """Get genders breakdown"""

        return []

    def __get_world_bubble_maps_coordinates(self) -> dict[str, list[dict]]:
        """Get world bubble maps coordinates"""

        world_bubble_maps_coordinates = {
            "coordinates_1": helpers.get_merged_flattened_list_of_dictionaries(
                data_lists=[
                    x.world_bubble_maps_coordinates.get("coordinates_1")
                    for x in self.__campaigns_data_q1
                    if x.world_bubble_maps_coordinates
                ],
                by_key="location_code",
                keys_to_merge=["n"],
            ),
            "coordinates_2": helpers.get_merged_flattened_list_of_dictionaries(
                data_lists=[
                    x.world_bubble_maps_coordinates.get("coordinates_2")
                    for x in self.__campaigns_data_q1
                    if x.world_bubble_maps_coordinates
                ],
                by_key="location_code",
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

        # Create a list containing all ages
        list_of_all_ages: list[str] = []
        for campaign_data in self.__campaigns_data_q1:
            if filter_seq == "1":
                campaign_data_list_of_ages = campaign_data.list_of_ages_1
            elif filter_seq == "2":
                campaign_data_list_of_ages = campaign_data.list_of_ages_2
            else:
                campaign_data_list_of_ages = []

            list_of_all_ages.extend(campaign_data_list_of_ages)

        # Calculate average age
        df = pd.DataFrame(list_of_all_ages, columns=["age"])
        average_age = "N/A"
        if len(df.index) > 0:
            average_age = " ".join(df["age"].mode())
            average_age = (
                average_age if helpers.contains_letters(average_age) else average_age
            )

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
            if campaign.campaign_code == CampaignCode.what_young_people_want.value:
                if filter_seq == "1":
                    return campaign.filter_1_description
                if filter_seq == "2":
                    return campaign.filter_2_description

        return ""

    def __get_country_options(self) -> list[dict]:
        """Get country options"""

        country_options = helpers.get_unique_flattened_list_of_dictionaries(
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

        country_regions_options = helpers.get_unique_flattened_list_of_dictionaries(
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

        response_topics_options = helpers.get_unique_flattened_list_of_dictionaries(
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

    def __get_age_ranges_options(self) -> list[dict]:
        """Get age ranges options"""

        ages_range_options = helpers.get_unique_flattened_list_of_dictionaries(
            data_lists=[
                [y for y in x.get("age_ranges_default") or []]
                for x in self.__campaigns_filter_options
            ]
        )

        return ages_range_options

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
