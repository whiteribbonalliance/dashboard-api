"""
MIT License

Copyright (c) 2023 World We Want. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

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

import copy
import re

import inflect
from pandas import DataFrame

from app import constants
from app import crud
from app.helpers import q_col_names
from app.schemas.filter import Filter

inflect_engine = inflect.engine()


def get_default_filter() -> Filter:
    """Get default filter"""

    return Filter(
        countries=[],
        regions=[],
        provinces=[],
        response_topics=[],
        only_responses_from_categories=False,
        genders=[],
        years=[],
        living_settings=[],
        professions=[],
        ages=[],
        age_buckets=[],
        only_multi_word_phrases_containing_filter_term=False,
        keyword_filter="",
        keyword_exclude="",
    )


def apply_filter_to_df(
    df: DataFrame, data_filter: Filter, campaign_crud: crud.Campaign, campaign_code: str
) -> DataFrame:
    """Apply filter to dataframe"""

    countries = data_filter.countries
    regions = data_filter.regions
    provinces = data_filter.provinces
    response_topics = data_filter.response_topics
    genders = data_filter.genders
    years = data_filter.years
    living_settings = data_filter.living_settings
    professions = data_filter.professions
    keyword_filter = data_filter.keyword_filter
    keyword_exclude = data_filter.keyword_exclude
    ages = data_filter.ages
    age_buckets = data_filter.age_buckets
    only_responses_from_categories = data_filter.only_responses_from_categories

    df_copy = df.copy()

    # Filter countries
    if countries:
        df_copy = df_copy[df_copy["alpha2country"].isin(countries)]

    # Filter using both regions and provinces
    if regions and provinces:
        df_copy = df_copy[
            df_copy[["region", "province"]].isin(regions + provinces).any(axis=1)
        ]
    else:
        # Filter only regions
        if regions:
            df_copy = df_copy[df_copy["region"].isin(regions)]

        # Filter only provinces
        elif provinces:
            df_copy = df_copy[df_copy["province"].isin(provinces)]

    # Filter genders
    if genders:
        df_copy = df_copy[df_copy["gender"].isin(genders)]

    # Filter years
    if years:
        df_copy = df_copy[df_copy["response_year"].isin(years)]

    # Filter living settings
    if living_settings:
        df_copy = df_copy[df_copy["setting"].isin(living_settings)]

    # Filter professions
    if professions:
        df_copy = df_copy[df_copy["profession"].isin(professions)]

    # Filter ages and age buckets
    if ages and age_buckets:
        # Filter using both ages and age buckets
        df_copy = df_copy[
            df_copy[["age", "age_bucket"]].isin(ages + age_buckets).any(axis=1)
        ]
    else:
        # Filter only ages
        if ages:
            df_copy = df_copy[df_copy["age"].isin(ages)]

        # Filter only age buckets
        elif age_buckets:
            df_copy = df_copy[df_copy["age_bucket"].isin(age_buckets)]

    def filter_by_response_topics(row_topics_str: str, topics: list[str]):
        """Filter by response topics"""

        if row_topics_str:
            for row_topic in row_topics_str.split("/"):
                for topic in topics:
                    if row_topic.strip() == topic.strip():
                        return True

        return False

    def filter_by_response_topic(row_topics_str: str, topic: str):
        """Filter by response topic"""

        if row_topics_str:
            if topic.strip() in [x.strip() for x in row_topics_str.split("/")]:
                return True

        return False

    # Apply the filter on specific columns for q1, q2 etc.
    campaign_q_codes = campaign_crud.get_q_codes()
    for q_code in campaign_q_codes:
        # Set column names based on question code
        canonical_code_column_name = q_col_names.get_canonical_code_col_name(
            q_code=q_code, campaign_code=campaign_code
        )

        lemmatized_column_name = q_col_names.get_lemmatized_col_name(q_code=q_code)
        parent_category_col_name = q_col_names.get_parent_category_col_name(
            q_code=q_code
        )

        # Filter response topics
        if len(response_topics) > 0:
            if only_responses_from_categories:
                condition = ~df_copy[canonical_code_column_name].isin(
                    {"xxxx"}
                )  # dummy series always True
            else:
                condition = df_copy[canonical_code_column_name].apply(
                    lambda x: filter_by_response_topics(x, response_topics)
                ) | df_copy[parent_category_col_name].apply(
                    lambda x: filter_by_response_topics(
                        row_topics_str=x, topics=response_topics
                    )
                )

            for response_topic in response_topics:
                if only_responses_from_categories:
                    condition &= df_copy[canonical_code_column_name].apply(
                        lambda x: filter_by_response_topic(x, response_topic)
                    )
                else:
                    condition |= df_copy[canonical_code_column_name].apply(
                        lambda x: filter_by_response_topic(x, response_topic)
                    )

            df_copy = df_copy[condition]

        # Filter keyword
        if keyword_filter:
            text_re = r"\b" + re.escape(keyword_filter.lower())
            df_copy = df_copy[
                df_copy[lemmatized_column_name].str.contains(text_re, regex=True)
            ]

        # Filter keyword exclude
        if keyword_exclude:
            text_exclude_re = r"\b" + re.escape(keyword_exclude.lower())
            df_copy = df_copy[
                ~df_copy[lemmatized_column_name].str.contains(
                    text_exclude_re, regex=True
                )
            ]

    return df_copy


def generate_description_of_filter(
    data_filter: Filter,
    respondents_count: int,
    respondent_noun_singular: str,
    respondent_noun_plural: str,
    response_topics_as_descriptions: list[str],
):
    countries = data_filter.countries
    regions = data_filter.regions
    provinces = data_filter.provinces
    genders = data_filter.genders
    professions = data_filter.professions
    keyword_filter = data_filter.keyword_filter
    keyword_exclude = data_filter.keyword_exclude
    ages = data_filter.ages + data_filter.age_buckets
    only_responses_from_categories = data_filter.only_responses_from_categories

    # Professions
    if len(professions) == 0:
        if respondents_count == 1:
            respondent = respondent_noun_singular
        else:
            respondent = respondent_noun_plural
    else:
        if respondents_count == 1:
            respondent = join_list_comma_and(professions, lower_words=True)
        else:
            respondent = join_list_comma_and(
                [inflect_engine.plural(p) for p in professions], lower_words=True
            )

    # Countries
    if len(countries) > 0:
        demonyms = []
        for country in countries:
            country_data = constants.COUNTRIES_DATA.get(country)
            if country_data:
                demonyms.append(country_data["demonym"])

        if demonyms:
            description = (
                f"{join_list_comma_and(demonyms, lower_words=False)} {respondent}"
            )
        else:
            description = ""
    else:
        description = respondent

    # Genders
    if genders is not None and len(genders) > 0:
        stated_genders = [
            gender for gender in genders if gender.lower() != "prefer not to say"
        ]
        if len(stated_genders) > 0:
            description = (
                join_list_comma_or(stated_genders, lower_words=True) + " " + description
            )
        if "prefer not to say" in [x.lower() for x in genders]:
            description += " who did not give a gender"

    # Regions and provinces
    if len(regions + provinces) > 0:
        description += " in " + join_list_comma_or(
            regions + provinces, lower_words=False
        )

    # Ages
    if ages is not None and len(ages) > 0:
        description += generate_age_description(ages=ages)

    if len(response_topics_as_descriptions) > 0:
        if only_responses_from_categories:
            description += " who mentioned " + join_list_comma_and(
                response_topics_as_descriptions, lower_words=True
            )
        else:
            description += " who mentioned " + join_list_comma_or(
                response_topics_as_descriptions, lower_words=True
            )

    # Keywords
    if len(keyword_filter) > 0:
        if len(response_topics_as_descriptions) == 0:
            description += " who mentioned "
        else:
            description += " and "
        description += '"' + str(keyword_filter).lower() + '"'

    # Keywords exclude
    if len(keyword_exclude) > 0:
        if len(response_topics_as_descriptions) > 0:
            description += ' but not "' + str(keyword_exclude) + '"'
        else:
            description += ' who did not mention "' + str(keyword_exclude) + '"'

    if description == respondent:
        description = "all " + respondent

    # Capitalize first letter only
    if description:
        description = capitalize_first_letter(text=description)

    return description


def check_if_filters_are_identical(
    filter_1: Filter | None, filter_2: Filter | None
) -> bool:
    """
    Find out if both sets of filters are identical.
    If both filters are identical then we should not display dual graphs.
    Some filters are nested lists, so they should be un-nested before performing the check.
    """

    if filter_1:
        data_filter_1 = copy.deepcopy(filter_1)
    else:
        data_filter_1 = None

    if filter_2:
        data_filter_2 = copy.deepcopy(filter_2)
    else:
        data_filter_2 = None

    if not data_filter_1 and not data_filter_2:
        return True
    if data_filter_1 and not data_filter_2:
        return False
    if data_filter_2 and not data_filter_1:
        return False

    data_filter_1.countries = flatten(data_filter_1.countries)
    data_filter_2.countries = flatten(data_filter_2.countries)

    data_filter_1.regions = flatten(data_filter_1.regions)
    data_filter_2.regions = flatten(data_filter_2.regions)

    data_filter_1.provinces = flatten(data_filter_1.provinces)
    data_filter_2.provinces = flatten(data_filter_2.provinces)

    data_filter_1.response_topics = flatten(data_filter_1.response_topics)
    data_filter_2.response_topics = flatten(data_filter_2.response_topics)

    data_filter_1.genders = flatten(data_filter_1.genders)
    data_filter_2.genders = flatten(data_filter_2.genders)

    data_filter_1.professions = flatten(data_filter_1.professions)
    data_filter_2.professions = flatten(data_filter_2.professions)

    return (
        data_filter_1.countries == data_filter_2.countries
        and data_filter_1.regions == data_filter_2.regions
        and data_filter_1.provinces == data_filter_2.provinces
        and data_filter_1.response_topics == data_filter_2.response_topics
        and data_filter_1.only_responses_from_categories
        == data_filter_2.only_responses_from_categories
        and data_filter_1.only_multi_word_phrases_containing_filter_term
        == data_filter_2.only_multi_word_phrases_containing_filter_term
        and data_filter_1.ages == data_filter_2.ages
        and data_filter_1.genders == data_filter_2.genders
        and data_filter_1.professions == data_filter_2.professions
        and data_filter_1.keyword_filter == data_filter_2.keyword_filter
        and data_filter_1.keyword_exclude == data_filter_2.keyword_exclude
    )


def check_if_filter_is_default(data_filter: Filter) -> bool:
    """Check if filter is default"""

    return check_if_filters_are_identical(
        filter_1=data_filter, filter_2=get_default_filter()
    )


def flatten(list_to_flatten) -> list:
    return [item for sublist in list_to_flatten for item in sublist]


def join_list_comma_and(listed, lower_words: bool) -> str:
    listed = list(listed)

    if len(listed) == 1:
        if lower_words and isinstance(listed[0], str):
            return listed[0].lower()
        else:
            return listed[0]

    if lower_words:
        listed = [x.lower() for x in listed if isinstance(x, str)]

    return "{} and {}".format(", ".join(listed[:-1]), listed[-1])


def join_list_comma_or(listed, lower_words: bool) -> str:
    listed = list(listed)

    if len(listed) == 1:
        if lower_words and isinstance(listed[0], str):
            return listed[0].lower()
        else:
            return listed[0]

    if lower_words:
        listed = [x.lower() for x in listed if isinstance(x, str)]

    return "{} or {}".format(", ".join(listed[:-1]), listed[-1])


def generate_age_description(ages: list[str]) -> str:
    """Generate age description"""

    if ages is None or len(ages) == 0:
        return ""
    if len(ages) == 1 and ages[0] == "Prefer not to say":
        return " who did not give their age"

    groups = " or ".join([a for a in sorted(ages) if a != "Prefer not to say"])

    if "Prefer not to say" in ages:
        groups += " or who did not give their age"

    groups = re.sub("-19 or 20|-24 or 25|-34 or 35|-44 or 45|-54 or 55", "", groups)

    return " aged " + groups


def capitalize_first_letter(text: str) -> str:
    """Capitalize the first letter and leave the rest as is"""

    if len(text) > 0 and isinstance(text[0], str):
        text = text[:1].upper() + text[1:]

    return text
