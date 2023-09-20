"""
Handles processing of data and business logic for campaigns merged
"""

from statistics import mean

from app import helpers, constants
from app.enums.campaign_code import CampaignCode
from app.schemas.campaign import Campaign
from app.schemas.filter import Filter
from app.utils import filters


class CampaignsMergedService:
    def __init__(
        self,
        campaigns: list[Campaign],
        filter_1: Filter | None = None,
        filter_2: Filter | None = None,
    ):
        self.__campaigns = campaigns

        # Check if filters are identical or not
        self.__filters_are_identical = filters.check_if_filters_are_identical(
            filter_1=filter_1, filter_2=filter_2
        )

    def get_responses_sample(self) -> dict[str, list[dict] | list]:
        """Get responses sample"""

        responses_sample = {
            "columns": helpers.get_unique_flattened_list_of_dictionaries(
                data_lists=[
                    x.responses_sample.get("columns") for x in self.__campaigns
                ],
            ),
            "data": helpers.get_distributed_list_of_dictionaries(
                data_lists=[x.responses_sample.get("data") for x in self.__campaigns]
            ),
        }

        # Responses sample - (remove columns gender, region and profession)
        responses_sample["columns"] = [
            x
            for x in responses_sample["columns"]
            if x.get("id") not in {"gender", "region", "profession"}
        ]

        return responses_sample

    def get_responses_breakdown(self) -> list[dict]:
        """Get responses breakdown"""

        responses_breakdown = helpers.get_merged_flattened_list_of_dictionaries(
            data_lists=[x.responses_breakdown for x in self.__campaigns],
            by_key="code",
            keys_to_merge=["count_1", "count_2"],
        )

        # Responses breakdown (sorted)
        responses_breakdown = sorted(
            responses_breakdown, key=lambda d: d.get("count_1"), reverse=True
        )

        return responses_breakdown

    def get_living_settings_breakdown(self) -> list:
        """Get living settings breakdown"""

        return []

    def get_top_words_and_phrases(self) -> dict[str, list[dict]]:
        """Get top words and phrases"""

        top_words_and_phrases = {
            "top_words": helpers.get_distributed_list_of_dictionaries(
                data_lists=[
                    x.top_words_and_phrases.get("top_words") for x in self.__campaigns
                ],
                sort_by_key="count_1",
                n_items=25,
                skip_list_size_check=True,
            ),
            "two_word_phrases": helpers.get_distributed_list_of_dictionaries(
                data_lists=[
                    x.top_words_and_phrases.get("two_word_phrases")
                    for x in self.__campaigns
                ],
                sort_by_key="count_1",
                n_items=25,
                skip_list_size_check=True,
            ),
            "three_word_phrases": helpers.get_distributed_list_of_dictionaries(
                data_lists=[
                    x.top_words_and_phrases.get("three_word_phrases")
                    for x in self.__campaigns
                ],
                sort_by_key="count_1",
                n_items=25,
                skip_list_size_check=True,
            ),
            "wordcloud_words": helpers.get_distributed_list_of_dictionaries(
                data_lists=[
                    x.top_words_and_phrases.get("wordcloud_words")
                    for x in self.__campaigns
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

    def get_histogram(self) -> dict[str, list | list[dict]]:
        """Get histogram"""

        histogram = {
            "ages": [],
            "age_ranges": [],
            "genders": [],
            "professions": [],
            "canonical_countries": helpers.get_merged_flattened_list_of_dictionaries(
                data_lists=[
                    x.histogram.get("canonical_countries") for x in self.__campaigns
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

    def get_genders_breakdown(self) -> list:
        """Get genders breakdown"""

        return []

    def get_world_bubble_maps_coordinates(self) -> dict[str, list[dict]]:
        """Get world bubble maps coordinates"""

        world_bubble_maps_coordinates = {
            "coordinates_1": helpers.get_merged_flattened_list_of_dictionaries(
                data_lists=[
                    x.world_bubble_maps_coordinates.get("coordinates_1")
                    for x in self.__campaigns
                ],
                by_key="location_code",
                keys_to_merge=["n"],
            ),
            "coordinates_2": helpers.get_merged_flattened_list_of_dictionaries(
                data_lists=[
                    x.world_bubble_maps_coordinates.get("coordinates_2")
                    for x in self.__campaigns
                ],
                by_key="location_code",
                keys_to_merge=["n"],
            ),
        }

        return world_bubble_maps_coordinates

    def get_filter_1_respondents_count(self) -> int:
        """Get filter 1 respondents count"""

        return sum([x.filter_1_respondents_count for x in self.__campaigns])

    def get_filter_2_respondents_count(self) -> int:
        """Get filter 2 respondents count"""

        return sum([x.filter_2_respondents_count for x in self.__campaigns])

    def get_filter_1_average_age(self) -> str:
        """Get filter 1 average age"""

        return str(
            mean(
                [
                    int(x.filter_1_average_age)
                    for x in self.__campaigns
                    if x.filter_1_average_age.isnumeric()
                ]
            )
        )

    def get_filter_2_average_age(self) -> str:
        """Get filter 2 average age"""

        return str(
            mean(
                [
                    int(x.filter_2_average_age)
                    for x in self.__campaigns
                    if x.filter_2_average_age.isnumeric()
                ]
            )
        )

    def get_filters_are_identical(self):
        """Get filters are identical"""

        return self.__filters_are_identical

    def get_filter_1_description(self) -> str:
        """
        Get filter 1 description.

        Use filter description from 'what_young_people_want' as this campaign uses respondent_noun as respondent.
        """

        for campaign in self.__campaigns:
            if campaign.campaign_code == CampaignCode.what_young_people_want.value:
                return campaign.filter_1_description

        return ""

    def get_filter_2_description(self) -> str:
        """
        Get filter 2 description.

        Use filter description from 'what_young_people_want' as this campaign uses respondent_noun as respondent.
        """

        for campaign in self.__campaigns:
            if campaign.campaign_code == CampaignCode.what_young_people_want.value:
                return campaign.filter_2_description

        return ""
