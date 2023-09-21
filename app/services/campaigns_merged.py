"""
Handles processing of data and business logic for campaigns merged
"""

from statistics import mean

from app import helpers, constants
from app.enums.campaign_code import CampaignCode
from app.schemas.campaign import Campaign
from app.schemas.filter import Filter
from app.schemas.filter_options import FilterOptions
from app.utils import filters


class CampaignsMergedService:
    def __init__(
        self,
        campaigns: list[Campaign] = None,
        campaigns_filter_options: list[dict] = None,
        campaigns_who_the_people_are_options: list[list[dict]] = None,
        filter_1: Filter | None = None,
        filter_2: Filter | None = None,
    ):
        if campaigns:
            self.__campaigns = campaigns
        else:
            self.__campaigns: list[Campaign] = []

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

        # Check if filters are identical or not
        self.__filters_are_identical = filters.check_if_filters_are_identical(
            filter_1=filter_1, filter_2=filter_2
        )

    def __get_responses_sample(self) -> dict[str, list[dict] | list]:
        """Get responses sample"""

        responses_sample = {
            "columns": helpers.get_unique_flattened_list_of_dictionaries(
                data_lists=[
                    x.responses_sample.get("columns")
                    for x in self.__campaigns
                    if x.responses_sample
                ],
            ),
            "data": helpers.get_distributed_list_of_dictionaries(
                data_lists=[
                    x.responses_sample.get("data")
                    for x in self.__campaigns
                    if x.responses_sample
                ],
                n_items=1000,
                shuffle=True,
            ),
        }

        # Responses sample - (keep only columns raw_response, description, canonical_country and age)
        columns_to_keep = {"raw_response", "description", "canonical_country", "age"}
        responses_sample["columns"] = [
            x for x in responses_sample["columns"] if x["id"] in columns_to_keep
        ]

        return responses_sample

    def __get_responses_breakdown(self) -> list[dict]:
        """Get responses breakdown"""

        responses_breakdown = helpers.get_merged_flattened_list_of_dictionaries(
            data_lists=[
                x.responses_breakdown for x in self.__campaigns if x.responses_breakdown
            ],
            by_key="code",
            keys_to_merge=["count_1", "count_2"],
        )

        # Responses breakdown (sorted)
        responses_breakdown = sorted(
            responses_breakdown, key=lambda d: d.get("count_1"), reverse=True
        )

        return responses_breakdown

    def __get_living_settings_breakdown(self) -> list:
        """Get living settings breakdown"""

        return []

    def __get_top_words_and_phrases(self) -> dict[str, list[dict]]:
        """Get top words and phrases"""

        top_words_and_phrases = {
            "top_words": helpers.get_distributed_list_of_dictionaries(
                data_lists=[
                    x.top_words_and_phrases.get("top_words")
                    for x in self.__campaigns
                    if x.top_words_and_phrases
                ],
                sort_by_key="count_1",
                n_items=25,
                skip_list_size_check=True,
            ),
            "two_word_phrases": helpers.get_distributed_list_of_dictionaries(
                data_lists=[
                    x.top_words_and_phrases.get("two_word_phrases")
                    for x in self.__campaigns
                    if x.top_words_and_phrases
                ],
                sort_by_key="count_1",
                n_items=25,
                skip_list_size_check=True,
            ),
            "three_word_phrases": helpers.get_distributed_list_of_dictionaries(
                data_lists=[
                    x.top_words_and_phrases.get("three_word_phrases")
                    for x in self.__campaigns
                    if x.top_words_and_phrases
                ],
                sort_by_key="count_1",
                n_items=25,
                skip_list_size_check=True,
            ),
            "wordcloud_words": helpers.get_distributed_list_of_dictionaries(
                data_lists=[
                    x.top_words_and_phrases.get("wordcloud_words")
                    for x in self.__campaigns
                    if x.top_words_and_phrases
                ],
                sort_by_key="value",
                n_items=100,
                skip_list_size_check=True,
            ),
        }

        # Top words or phrases (merged)
        top_words_and_phrases[
            "top_words"
        ] = helpers.get_merged_flattened_list_of_dictionaries(
            data_lists=[top_words_and_phrases["top_words"]],
            by_key="word",
            keys_to_merge=["count_1", "count_2"],
        )
        top_words_and_phrases[
            "two_word_phrases"
        ] = helpers.get_merged_flattened_list_of_dictionaries(
            data_lists=[top_words_and_phrases["two_word_phrases"]],
            by_key="word",
            keys_to_merge=["count_1", "count_2"],
        )
        top_words_and_phrases[
            "three_word_phrases"
        ] = helpers.get_merged_flattened_list_of_dictionaries(
            data_lists=[top_words_and_phrases["three_word_phrases"]],
            by_key="word",
            keys_to_merge=["count_1", "count_2"],
        )
        top_words_and_phrases[
            "wordcloud_words"
        ] = helpers.get_merged_flattened_list_of_dictionaries(
            data_lists=[top_words_and_phrases["wordcloud_words"]],
            by_key="text",
            keys_to_merge=["value"],
        )

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
            key=lambda d: d.get("value"),
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
                    for x in self.__campaigns
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
                    for x in self.__campaigns
                    if x.world_bubble_maps_coordinates
                ],
                by_key="location_code",
                keys_to_merge=["n"],
            ),
            "coordinates_2": helpers.get_merged_flattened_list_of_dictionaries(
                data_lists=[
                    x.world_bubble_maps_coordinates.get("coordinates_2")
                    for x in self.__campaigns
                    if x.world_bubble_maps_coordinates
                ],
                by_key="location_code",
                keys_to_merge=["n"],
            ),
        }

        return world_bubble_maps_coordinates

    def __get_filter_1_respondents_count(self) -> int:
        """Get filter 1 respondents count"""

        filter_1_respondents_counts: list[int] = [
            x.filter_1_respondents_count for x in self.__campaigns
        ]
        if not filter_1_respondents_counts:
            filter_1_respondents_counts = [0]

        return sum(filter_1_respondents_counts)

    def __get_filter_2_respondents_count(self) -> int:
        """Get filter 2 respondents count"""

        filter_2_respondents_counts: list[int] = [
            x.filter_2_respondents_count for x in self.__campaigns
        ]
        if not filter_2_respondents_counts:
            filter_2_respondents_counts = [0]

        return sum(filter_2_respondents_counts)

    def __get_filter_1_average_age(self) -> str:
        """Get filter 1 average age"""

        filter_1_ages = [
            int(x.filter_1_average_age)
            for x in self.__campaigns
            if x.filter_1_average_age.isnumeric()
        ]

        if not filter_1_ages:
            filter_1_ages = [0]

        return str(round(mean(filter_1_ages)))

    def __get_filter_2_average_age(self) -> str:
        """Get filter 2 average age"""

        filter_2_ages = [
            int(x.filter_2_average_age)
            for x in self.__campaigns
            if x.filter_2_average_age.isnumeric()
        ]

        if not filter_2_ages:
            filter_2_ages = [0]

        return str(round(mean(filter_2_ages)))

    def __get_filters_are_identical(self) -> bool:
        """Get filters are identical"""

        return self.__filters_are_identical

    def __get_filter_1_description(self) -> str:
        """
        Get filter 1 description.

        Use filter description from 'what_young_people_want' as this campaign uses respondent_noun as respondent.
        """

        for campaign in self.__campaigns:
            if campaign.campaign_code == CampaignCode.what_young_people_want.value:
                return campaign.filter_1_description

        return ""

    def __get_filter_2_description(self) -> str:
        """
        Get filter 2 description.

        Use filter description from 'what_young_people_want' as this campaign uses respondent_noun as respondent.
        """

        for campaign in self.__campaigns:
            if campaign.campaign_code == CampaignCode.what_young_people_want.value:
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

        country_regions_options = helpers.get_merged_flattened_list_of_dictionaries(
            data_lists=[
                [y for y in x.get("country_regions") or []]
                for x in self.__campaigns_filter_options
            ],
            by_key="country_alpha2_code",
            keys_to_merge=[],
        )

        # Sort
        country_regions_options = sorted(
            country_regions_options, key=lambda x: x["country_alpha2_code"]
        )

        return country_regions_options

    def __get_response_topics_options(self) -> list[dict]:
        """Get response topic options"""

        response_topics_options = helpers.get_merged_flattened_list_of_dictionaries(
            data_lists=[
                [y for y in x.get("response_topics") or []]
                for x in self.__campaigns_filter_options
            ],
            by_key="value",
            keys_to_merge=[],
        )

        return response_topics_options

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
        filter_1_respondents_count = self.__get_filter_1_respondents_count()

        # Filter 2 respondents count
        filter_2_respondents_count = self.__get_filter_2_respondents_count()

        # Filter 1 average age
        filter_1_average_age = self.__get_filter_1_average_age()

        # Filter 2 average age
        filter_2_average_age = self.__get_filter_2_average_age()

        # Filter 1 description
        filter_1_description = self.__get_filter_1_description()

        # Filter 2 description
        filter_2_description = self.__get_filter_2_description()

        # Filters are identical
        filters_are_identical = self.__get_filters_are_identical()

        return Campaign(
            campaign_code="",
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
            ages=[],
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
