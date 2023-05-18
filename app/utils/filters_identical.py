from app.schemas.filter_options import FilterOptions


def get_filters_identical(
    filter_options_1: FilterOptions, filter_options_2: FilterOptions
):
    """
    Find out if both sets of filters are identical.
    If both filters are identical then we should not display dual graphs.
    Some filters are nested lists, so they should be un-nested before performing the check.

    :return:
    """

    filter_options_1.country = flatten(filter_options_1.country)
    filter_options_2.country = flatten(filter_options_2.country)

    filter_options_1.region = flatten(filter_options_1.region)
    filter_options_2.region = flatten(filter_options_2.region)

    filter_options_1.topic = flatten(filter_options_1.topic)
    filter_options_2.topic = flatten(filter_options_2.topic)

    filter_options_1.gender = flatten(filter_options_1.gender)
    filter_options_2.gender = flatten(filter_options_2.gender)

    filter_options_1.profession = flatten(filter_options_1.profession)
    filter_options_2.profession = flatten(filter_options_2.profession)

    return (
        filter_options_1.country == filter_options_2.country
        and filter_options_1.region == filter_options_2.region
        and filter_options_1.topic == filter_options_2.topic
        and filter_options_1.match_categories == filter_options_2.match_categories
        and filter_options_1.age == filter_options_2.age
        and filter_options_1.gender == filter_options_2.gender
        and filter_options_1.profession == filter_options_2.profession
        and filter_options_1.keyword_filter == filter_options_2.keyword_filter
        and filter_options_1.keyword_exclude == filter_options_2.keyword_exclude
    )


def flatten(list_to_flatten) -> list:
    return [item for sublist in list_to_flatten for item in sublist]
