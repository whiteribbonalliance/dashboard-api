import re

import inflect
from pandas import DataFrame

from app.enums.campaign_code import CampaignCode
from app.schemas.filter import Filter
from app.utils import code_hierarchy
from app.utils import countries_data_loader
from app.utils import data_reader

inflect_engine = inflect.engine()


def apply_filters(df: DataFrame, _filter: Filter) -> DataFrame:
    """Apply filter to dataframe"""

    countries = _filter.countries
    regions = _filter.regions
    response_topics = _filter.response_topics
    genders = _filter.genders
    professions = _filter.professions
    keyword_filter = _filter.keyword_filter
    keyword_exclude = _filter.keyword_exclude
    age_buckets = _filter.age_buckets
    only_multi_word_phrases_containing_filter_term = (
        _filter.only_multi_word_phrases_containing_filter_term
    )

    df_copy = df.copy()

    # Filter countries
    if len(countries) > 0:
        df_copy = df_copy[df_copy["alpha2country"].isin(countries)]

    # Filter regions
    if len(regions) > 0:
        df_copy = df_copy[df_copy["region"].isin(regions)]

    # Filter response topics
    if len(response_topics) > 0:
        if only_multi_word_phrases_containing_filter_term:
            condition = ~df_copy["canonical_code"].isin(
                {"xxxx"}
            )  # dummy series always True
        else:
            condition = df_copy["canonical_code"].isin(response_topics) | df_copy[
                "top_level"
            ].isin(response_topics)
        for response_topic in response_topics:
            if only_multi_word_phrases_containing_filter_term:
                condition &= df_copy["canonical_code"].str.contains(
                    r"\b" + response_topic + r"\b", regex=True
                )
            else:
                condition |= df_copy["canonical_code"].str.contains(
                    r"\b" + response_topic + r"\b", regex=True
                )
        df_copy = df_copy[condition]

    # Filter genders
    if len(genders) > 0:
        df_copy = df_copy[df_copy["gender"].isin(genders)]

    # Filter professions
    if len(professions) > 0:
        df_copy = df_copy[df_copy["professional_title"].isin(professions)]

    # Filter keyword
    if keyword_filter != "":
        text_re = r"\b" + re.escape(keyword_filter)
        df_copy = df_copy[df_copy["lemmatized"].str.contains(text_re, regex=True)]

    # Filter keyword exclude
    if keyword_exclude != "":
        text_exclude_re = r"\b" + re.escape(keyword_exclude)
        df_copy = df_copy[
            ~df_copy["lemmatized"].str.contains(text_exclude_re, regex=True)
        ]

    # Filter age buckets
    if len(age_buckets) > 0:
        df_copy = df_copy[df_copy["age_bucket"].isin(age_buckets)]

    return df_copy


def generate_description_of_filter(
    campaign_code: CampaignCode,
    _filter: Filter,
    num_results,
):
    countries = _filter.countries
    regions = _filter.regions
    response_topics = _filter.response_topics
    genders = _filter.genders
    professions = _filter.professions
    keyword_filter = _filter.keyword_filter
    keyword_exclude = _filter.keyword_exclude
    age_buckets = _filter.age_buckets
    only_responses_from_categories = _filter.only_responses_from_categories

    data_readerr = data_reader.DataReader(campaign_code=campaign_code)

    professions_from_databank = data_readerr.get_professions()
    genders_from_databank = data_readerr.get_genders()

    respondent_noun_singular = data_readerr.get_respondent_noun_singular()
    respondent_noun_plural = data_readerr.get_respondent_noun_plural()

    if len(professions) == 0 or set(professions) == set(professions_from_databank):
        if num_results == 1:
            women = respondent_noun_singular
        else:
            women = respondent_noun_plural
    else:
        if num_results == 1:
            women = join_list_comma_and(professions)
        else:
            women = join_list_comma_and([inflect_engine.plural(p) for p in professions])

    countries_data = countries_data_loader.get_countries_data_list()

    if len(countries) > 0:
        demonyms = []
        for country in countries:
            country_data = countries_data.get(country)
            if not country_data:
                # TODO: log?
                continue

            demonyms.append(country_data["demonym"])

        if demonyms:
            description = f"{join_list_comma_and(demonyms)} {women}"
        else:
            description = ""
    else:
        description = women
    if (
        genders is not None
        and len(genders) > 0
        and set(genders) != set(genders_from_databank)
    ):
        stated_genders = [gender for gender in genders if gender != "prefer not to say"]
        if len(stated_genders) > 0:
            description = join_list_comma_or(stated_genders) + " " + description
        if "prefer not to say" in genders:
            description += " who did not give a gender"

    if len(regions) > 0:
        description += " in " + join_list_comma_or(regions)

    if age_buckets is not None and len(age_buckets) > 0:
        description += generate_age_description(
            campaign_code=campaign_code, age_buckets=age_buckets
        )

    mapping_to_description = code_hierarchy.get_mapping_to_description(
        campaign_code=campaign_code
    )
    response_topics_mentioned = list(
        [
            mapping_to_description.get(response_topic, response_topic)
            for response_topic in response_topics
        ]
    )
    if len(response_topics_mentioned) > 0:
        if only_responses_from_categories:
            description += " who mentioned " + join_list_comma_and(
                response_topics_mentioned
            )
        else:
            description += " who mentioned " + join_list_comma_or(
                response_topics_mentioned
            )

    if len(keyword_filter) > 0:
        if len(response_topics_mentioned) == 0:
            description += " who mentioned "
        else:
            description += " and "
        description += '"' + str(keyword_filter) + '"'

    if len(keyword_exclude) > 0:
        if len(response_topics_mentioned) > 0:
            description += ' but not "' + str(keyword_exclude) + '"'
        else:
            description += ' who did not mention "' + str(keyword_exclude) + '"'

    if description == women:
        description = "all " + women

    # Capitalize
    if description:
        description = description.capitalize()

    return description


def check_if_filters_are_identical(
    filter_options_1: Filter, filter_options_2: Filter
) -> bool:
    """
    Find out if both sets of filters are identical.
    If both filters are identical then we should not display dual graphs.
    Some filters are nested lists, so they should be un-nested before performing the check.
    """

    filter_options_1.country = flatten(filter_options_1.country)
    filter_options_2.country = flatten(filter_options_2.country)

    filter_options_1.region = flatten(filter_options_1.region)
    filter_options_2.region = flatten(filter_options_2.region)

    filter_options_1.response_topic = flatten(filter_options_1.response_topic)
    filter_options_2.response_topic = flatten(filter_options_2.response_topic)

    filter_options_1.gender = flatten(filter_options_1.gender)
    filter_options_2.gender = flatten(filter_options_2.gender)

    filter_options_1.profession = flatten(filter_options_1.profession)
    filter_options_2.profession = flatten(filter_options_2.profession)

    return (
        filter_options_1.country == filter_options_2.country
        and filter_options_1.region == filter_options_2.region
        and filter_options_1.response_topic == filter_options_2.response_topic
        and filter_options_1.only_responses_from_categories
        == filter_options_2.only_responses_from_categories
        and filter_options_1.only_multi_word_phrases_containing_filter_term
        == filter_options_2.only_multi_word_phrases_containing_filter_term
        and filter_options_1.age_buckets == filter_options_2.age_buckets
        and filter_options_1.gender == filter_options_2.gender
        and filter_options_1.profession == filter_options_2.profession
        and filter_options_1.keyword_filter == filter_options_2.keyword_filter
        and filter_options_1.keyword_exclude == filter_options_2.keyword_exclude
    )


def flatten(list_to_flatten) -> list:
    return [item for sublist in list_to_flatten for item in sublist]


def join_list_comma_and(listed) -> str:
    listed = list(listed)
    if len(listed) == 1:
        return listed[0]

    return "{} and {}".format(", ".join(listed[:-1]), listed[-1])


def join_list_comma_or(listed) -> str:
    listed = list(listed)
    if len(listed) == 1:
        return listed[0]

    return "{} or {}".format(", ".join(listed[:-1]), listed[-1])


def generate_age_description(
    campaign_code: CampaignCode, age_buckets: list[str]
) -> str:
    """Generate age description"""

    data_readerr = data_reader.DataReader(campaign_code=campaign_code)

    age_buckets_from_databank = data_readerr.get_age_buckets()

    if (
        age_buckets is None
        or len(age_buckets) == 0
        or set(age_buckets) == set(age_buckets_from_databank)
    ):
        return ""
    if len(age_buckets) == 1 and age_buckets[0] == "prefer not to say":
        return " who did not give their age"

    groups = " or ".join([a for a in sorted(age_buckets) if a != "prefer not to say"])

    if "prefer not to say" in age_buckets:
        groups += " or who did not give their age"

    groups = re.sub("-19 or 20|-24 or 25|-34 or 35|-44 or 45|-54 or 55", "", groups)

    return " aged " + groups
