import logging
from statistics import mean
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app import helpers
from app.api import dependencies
from app.api.v1.endpoints import campaigns as campaigns_endpoints
from app.enums.campaign_code import CampaignCode
from app.logginglib import init_custom_logger
from app.schemas.campaign import Campaign
from app.schemas.campaign_request import CampaignRequest
from app.schemas.common_parameters_all_campaigns import CommonParametersAllCampaigns
from app.schemas.common_parameters_campaign import CommonParametersCampaign
from app.services.api_cache import ApiCache
from app.utils import filters

logger = logging.getLogger(__name__)
init_custom_logger(logger)

router = APIRouter(prefix="/all-campaigns")

api_cache = ApiCache()


@router.post(
    path="",
    response_model=Campaign,
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
async def read_all_campaigns(
    parameters: Annotated[
        CommonParametersAllCampaigns,
        Depends(dependencies.dep_common_parameters_all_campaigns),
    ],
    campaign_req: CampaignRequest,
):
    """Read all campaigns"""

    language = parameters.language
    request = parameters.request
    q_code = parameters.q_code

    filter_1_description = ""
    filter_2_description = ""

    # Get all campaigns
    campaigns: list[Campaign] = []
    for campaign_code in CampaignCode:
        # TODO: Temporarily skip campaign 'wee'
        if campaign_code == CampaignCode.womens_economic_empowerment:
            continue

        parameters = CommonParametersCampaign(
            campaign_code=campaign_code,
            language=language,
            request=request,
            q_code=q_code,
        )

        campaign = await campaigns_endpoints.read_campaign(
            parameters=parameters, campaign_req=campaign_req
        )

        # Set filter description from 'what_young_people_want' as this campaign uses respondent_noun as respondent
        if campaign_code == CampaignCode.what_young_people_want:
            filter_1_description = campaign.filter_1_description
            filter_2_description = campaign.filter_2_description

        campaigns.append(campaign)

    # Responses sample
    responses_sample = {
        "columns": helpers.get_unique_flattened_list_of_dictionaries(
            data_lists=[x.responses_sample.get("columns") for x in campaigns],
        ),
        "data": helpers.get_distributed_list_of_dictionaries(
            data_lists=[x.responses_sample.get("data") for x in campaigns]
        ),
    }

    # Responses breakdown
    responses_breakdown = helpers.get_distributed_list_of_dictionaries(
        data_lists=[x.responses_breakdown for x in campaigns], sort_by_key="count_1"
    )

    # Responses breakdown (sorted)
    responses_breakdown = sorted(
        responses_breakdown, key=lambda d: d.get("count_1"), reverse=True
    )

    # Living settings breakdown
    # living_settings_breakdown = helpers.get_distributed_list(
    #     data_lists=[x.living_settings_breakdown for x in campaigns]
    # )

    # Top words or phrases
    top_words_and_phrases = {
        "top_words": helpers.get_distributed_list_of_dictionaries(
            data_lists=[x.top_words_and_phrases.get("top_words") for x in campaigns],
            sort_by_key="count_1",
        ),
        "two_word_phrases": helpers.get_distributed_list_of_dictionaries(
            data_lists=[
                x.top_words_and_phrases.get("two_word_phrases") for x in campaigns
            ],
            sort_by_key="count_1",
        ),
        "three_word_phrases": helpers.get_distributed_list_of_dictionaries(
            data_lists=[
                x.top_words_and_phrases.get("three_word_phrases") for x in campaigns
            ],
            sort_by_key="count_1",
        ),
        "wordcloud_words": helpers.get_distributed_list_of_dictionaries(
            data_lists=[
                x.top_words_and_phrases.get("wordcloud_words") for x in campaigns
            ],
            sort_by_key="value",
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
        top_words_and_phrases["top_words"], key=lambda d: d.get("count_1"), reverse=True
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

    # Histogram
    histogram = {
        "ages": [],
        "age_ranges": [],
        "genders": [],
        "professions": [],
        "canonical_countries": helpers.get_merged_flattened_list_of_dictionaries(
            data_lists=[x.histogram.get("canonical_countries") for x in campaigns],
            by_key="name",
            keys_to_merge=["count_1", "count_2"],
        ),
    }

    # Histogram (sorted)
    # histogram["ages"] = sorted(
    #     histogram["ages"],
    #     key=lambda d: d.get("count_1"),
    #     reverse=True,
    # )
    # histogram["age_ranges"] = sorted(
    #     histogram["age_ranges"],
    #     key=lambda d: d.get("count_1"),
    #     reverse=True,
    # )
    # histogram["genders"] = sorted(
    #     histogram["genders"],
    #     key=lambda d: d.get("count_1"),
    #     reverse=True,
    # )
    # histogram["professions"] = sorted(
    #     histogram["professions"],
    #     key=lambda d: d.get("count_1"),
    #     reverse=True,
    # )
    histogram["canonical_countries"] = sorted(
        histogram["canonical_countries"],
        key=lambda d: d.get("count_1"),
        reverse=True,
    )

    # Genders breakdown
    # genders_breakdown = helpers.get_distributed_list(
    #     data_lists=[x.genders_breakdown for x in campaigns], sort_by_key="count"
    # )

    # World bubble maps coordinates
    world_bubble_maps_coordinates = {
        "coordinates_1": helpers.get_merged_flattened_list_of_dictionaries(
            data_lists=[
                x.world_bubble_maps_coordinates.get("coordinates_1") for x in campaigns
            ],
            by_key="location_code",
            keys_to_merge=["n"],
        ),
        "coordinates_2": helpers.get_merged_flattened_list_of_dictionaries(
            data_lists=[
                x.world_bubble_maps_coordinates.get("coordinates_2") for x in campaigns
            ],
            by_key="location_code",
            keys_to_merge=["n"],
        ),
    }

    # Filter 1 respondents count
    filter_1_respondents_count = sum([x.filter_1_respondents_count for x in campaigns])

    # Filter 2 respondents count
    filter_2_respondents_count = sum([x.filter_2_respondents_count for x in campaigns])

    # Filter 1 average age
    filter_1_average_age = str(
        mean(
            [
                int(x.filter_1_average_age)
                for x in campaigns
                if x.filter_1_average_age.isnumeric()
            ]
        )
    )

    # Filter 2 average age
    filter_2_average_age = str(
        mean(
            [
                int(x.filter_2_average_age)
                for x in campaigns
                if x.filter_2_average_age.isnumeric()
            ]
        )
    )

    # Filters are identical
    filters_are_identical = filters.check_if_filters_are_identical(
        filter_1=campaign_req.filter_1, filter_2=campaign_req.filter_2
    )

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
