import re

import inflect
from pandas import DataFrame

from app import constants
from app.enums.campaign_code import CampaignCode
from app.enums.question_code import QuestionCode
from app.schemas.filter import Filter
from app.utils import code_hierarchy

inflect_engine = inflect.engine()


def get_default_filter() -> Filter:
    """Get default filter"""

    return Filter(
        countries=[],
        regions=[],
        response_topics=[],
        only_responses_from_categories=False,
        genders=[],
        professions=[],
        ages=[],
        only_multi_word_phrases_containing_filter_term=False,
        keyword_filter="",
        keyword_exclude="",
    )


def apply_filter_to_df(
    df: DataFrame, _filter: Filter, campaign_code: CampaignCode
) -> DataFrame:
    """Apply filter to dataframe"""

    countries = _filter.countries
    regions = _filter.regions
    response_topics = _filter.response_topics
    genders = _filter.genders
    professions = _filter.professions
    keyword_filter = _filter.keyword_filter
    keyword_exclude = _filter.keyword_exclude
    ages = _filter.ages
    only_responses_from_categories = _filter.only_responses_from_categories

    df_copy = df.copy()

    question_codes = [QuestionCode.q1]
    if campaign_code in constants.CAMPAIGNS_WITH_Q2:
        question_codes.append(QuestionCode.q2)

    # Apply the filter for q1, q2 etc.
    for q_code in question_codes:
        # Set column names based on question code
        canonical_code_column_name = f"q{q_code.value}_canonical_code"
        lemmatized_column_name = f"q{q_code.value}_lemmatized"

        # Filter countries
        if len(countries) > 0:
            df_copy = df_copy[df_copy["alpha2country"].isin(countries)]

        # Filter regions
        if len(regions) > 0:
            df_copy = df_copy[df_copy["region"].isin(regions)]

        # Filter response topics
        if len(response_topics) > 0:
            if only_responses_from_categories:
                condition = ~df_copy[canonical_code_column_name].isin(
                    {"xxxx"}
                )  # dummy series always True
            else:
                condition = df_copy[canonical_code_column_name].isin(
                    response_topics
                ) | df_copy["q1_top_level"].isin(response_topics)
            for response_topic in response_topics:
                if only_responses_from_categories:
                    condition &= df_copy[canonical_code_column_name].str.contains(
                        r"\b" + response_topic + r"\b", regex=True
                    )
                else:
                    condition |= df_copy[canonical_code_column_name].str.contains(
                        r"\b" + response_topic + r"\b", regex=True
                    )

            df_copy = df_copy[condition]

        # Filter genders
        if len(genders) > 0:
            df_copy = df_copy[df_copy["gender"].isin(genders)]

        # Filter professions
        if len(professions) > 0:
            df_copy = df_copy[df_copy["profession"].isin(professions)]

        # Filter keyword
        if keyword_filter:
            text_re = r"\b" + re.escape(keyword_filter)
            df_copy = df_copy[
                df_copy[lemmatized_column_name].str.contains(text_re, regex=True)
            ]

        # Filter keyword exclude
        if keyword_exclude:
            text_exclude_re = r"\b" + re.escape(keyword_exclude)
            df_copy = df_copy[
                ~df_copy[lemmatized_column_name].str.contains(
                    text_exclude_re, regex=True
                )
            ]

        # Filter ages
        if len(ages) > 0:
            df_copy = df_copy[df_copy["age"].isin(ages)]

    return df_copy


def generate_description_of_filter(
    campaign_code: CampaignCode,
    _filter: Filter,
    num_results: int,
    respondent_noun_singular: str,
    respondent_noun_plural: str,
):
    countries = _filter.countries
    regions = _filter.regions
    response_topics = _filter.response_topics
    genders = _filter.genders
    professions = _filter.professions
    keyword_filter = _filter.keyword_filter
    keyword_exclude = _filter.keyword_exclude
    ages = _filter.ages
    only_responses_from_categories = _filter.only_responses_from_categories

    if len(professions) == 0:
        if num_results == 1:
            women = respondent_noun_singular
        else:
            women = respondent_noun_plural
    else:
        if num_results == 1:
            women = join_list_comma_and(professions)
        else:
            women = join_list_comma_and([inflect_engine.plural(p) for p in professions])

    if len(countries) > 0:
        demonyms = []
        for country in countries:
            country_data = constants.COUNTRIES_DATA.get(country)
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
    if genders is not None and len(genders) > 0:
        stated_genders = [gender for gender in genders if gender != "prefer not to say"]
        if len(stated_genders) > 0:
            description = join_list_comma_or(stated_genders) + " " + description
        if "prefer not to say" in genders:
            description += " who did not give a gender"

    if len(regions) > 0:
        description += " in " + join_list_comma_or(regions)

    if ages is not None and len(ages) > 0:
        description += generate_age_description(ages=ages)

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
    filter_1: Filter | None, filter_2: Filter | None
) -> bool:
    """
    Find out if both sets of filters are identical.
    If both filters are identical then we should not display dual graphs.
    Some filters are nested lists, so they should be un-nested before performing the check.
    """

    if not filter_1 and not filter_2:
        return True
    if filter_1 and not filter_2:
        return False
    if filter_2 and not filter_1:
        return False

    filter_1.countries = flatten(filter_1.countries)
    filter_2.countries = flatten(filter_2.countries)

    filter_1.regions = flatten(filter_1.regions)
    filter_2.regions = flatten(filter_2.regions)

    filter_1.response_topics = flatten(filter_1.response_topics)
    filter_2.response_topics = flatten(filter_2.response_topics)

    filter_1.genders = flatten(filter_1.genders)
    filter_2.genders = flatten(filter_2.genders)

    filter_1.professions = flatten(filter_1.professions)
    filter_2.professions = flatten(filter_2.professions)

    return (
        filter_1.countries == filter_2.countries
        and filter_1.regions == filter_2.regions
        and filter_1.response_topics == filter_2.response_topics
        and filter_1.only_responses_from_categories
        == filter_2.only_responses_from_categories
        and filter_1.only_multi_word_phrases_containing_filter_term
        == filter_2.only_multi_word_phrases_containing_filter_term
        and filter_1.ages == filter_2.ages
        and filter_1.genders == filter_2.genders
        and filter_1.professions == filter_2.professions
        and filter_1.keyword_filter == filter_2.keyword_filter
        and filter_1.keyword_exclude == filter_2.keyword_exclude
    )


def check_if_filter_is_default(_filter: Filter) -> bool:
    """Check if filter is default"""

    return check_if_filters_are_identical(
        filter_1=_filter, filter_2=get_default_filter()
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


def generate_age_description(ages: list[str]) -> str:
    """Generate age description"""

    if ages is None or len(ages) == 0:
        return ""
    if len(ages) == 1 and ages[0] == "prefer not to say":
        return " who did not give their age"

    groups = " or ".join([a for a in sorted(ages) if a != "prefer not to say"])

    if "prefer not to say" in ages:
        groups += " or who did not give their age"

    groups = re.sub("-19 or 20|-24 or 25|-34 or 35|-44 or 45|-54 or 55", "", groups)

    return " aged " + groups
