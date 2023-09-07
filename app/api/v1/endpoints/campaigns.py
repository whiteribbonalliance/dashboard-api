import logging
import os.path
from io import StringIO
from typing import Annotated

import pandas as pd
import requests
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app import databases, auth_handler
from app import http_exceptions
from app.api import dependencies
from app.crud.campaign import CampaignCRUD
from app.enums.campaign_code import CampaignCode
from app.logginglib import init_custom_logger
from app.schemas.campaign import Campaign
from app.schemas.campaign_request import CampaignRequest
from app.schemas.common_parameters_campaign import CommonParametersCampaign
from app.schemas.filter_options import FilterOptions
from app.schemas.option import Option
from app.schemas.parameters_campaign_data import (
    ParametersCampaignData,
)
from app.services import cloud_storage_interactions
from app.services.api_cache import ApiCache
from app.services.campaign import CampaignService
from app.services.translations_cache import TranslationsCache
from app.services.translator import Translator

logger = logging.getLogger(__name__)
init_custom_logger(logger)

router = APIRouter(prefix="/campaigns")

api_cache = ApiCache()


@router.post(
    path="/{campaign}",
    response_model=Campaign,
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
async def read_campaign(
    parameters: Annotated[
        CommonParametersCampaign, Depends(dependencies.dep_common_parameters_campaign)
    ],
    campaign_req: CampaignRequest,
):
    """Read a campaign"""

    campaign_code = parameters.campaign_code
    language = parameters.language
    q_code = parameters.q_code

    filter_1 = campaign_req.filter_1
    filter_2 = campaign_req.filter_2

    # Create service
    campaign_service = CampaignService(
        campaign_code=campaign_code,
        language=language,
        filter_1=filter_1,
        filter_2=filter_2,
    )

    # Top words and phrases
    top_words_and_phrases = {
        "top_words": campaign_service.get_top_words(q_code=q_code),
        "two_word_phrases": campaign_service.get_two_word_phrases(q_code=q_code),
        "three_word_phrases": campaign_service.get_three_word_phrases(q_code=q_code),
        "wordcloud_words": campaign_service.get_wordcloud_words(q_code=q_code),
    }

    # Responses sample
    responses_sample = {
        "columns": campaign_service.get_responses_sample_columns(q_code=q_code),
        "data": campaign_service.get_responses_sample(q_code=q_code),
    }

    # Responses breakdown
    responses_breakdown = campaign_service.get_responses_breakdown(q_code=q_code)

    # Living settings breakdown
    living_settings_breakdown = campaign_service.get_living_settings_breakdown()

    # Histogram
    histogram = campaign_service.get_histogram()

    # Genders breakdown
    if campaign_code == CampaignCode.what_young_people_want:
        genders_breakdown = campaign_service.get_genders_breakdown()
    else:
        genders_breakdown = []

    # World bubble maps coordinates
    world_bubble_maps_coordinates = campaign_service.get_world_bubble_maps_coordinates()

    # Respondents count
    filter_1_respondents_count = campaign_service.get_filter_1_respondents_count()
    filter_2_respondents_count = campaign_service.get_filter_2_respondents_count()

    # Average age
    filter_1_average_age = campaign_service.get_filter_1_average_age()
    filter_2_average_age = campaign_service.get_filter_2_average_age()

    # Filters Description
    filter_1_description = campaign_service.get_filter_1_description()
    filter_2_description = campaign_service.get_filter_2_description()

    # Filters are identical
    filters_are_identical = campaign_service.get_filters_are_identical()

    # Translate
    try:
        if language != "en" and TranslationsCache().is_loaded():
            translator = Translator()
            translator.set_target_language(target_language=language)

            # Extract texts
            translator.apply_t_function_campaign(
                t=translator.extract_text,
                campaign_code=campaign_code,
                language=language,
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

            # Apply translations to texts
            (
                responses_sample,
                responses_breakdown,
                living_settings_breakdown,
                top_words_and_phrases,
                histogram,
                genders_breakdown,
                world_bubble_maps_coordinates,
                filter_1_average_age,
                filter_2_average_age,
                filter_1_description,
                filter_2_description,
            ) = translator.apply_t_function_campaign(
                t=translator.translate_text,
                campaign_code=campaign_code,
                language=language,
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
    except (Exception,) as e:
        logger.warning(f"An error occurred during translation of 'campaign': {str(e)}")

    return Campaign(
        responses_sample=responses_sample,
        responses_breakdown=responses_breakdown,
        living_settings_breakdown=living_settings_breakdown,
        top_words_and_phrases=top_words_and_phrases,
        histogram=histogram,
        genders_breakdown=genders_breakdown,
        world_bubble_maps_coordinates=world_bubble_maps_coordinates,
        filter_1_respondents_count=filter_1_respondents_count,
        filter_2_respondents_count=filter_2_respondents_count,
        filter_1_average_age=filter_1_average_age,
        filter_2_average_age=filter_2_average_age,
        filter_1_description=filter_1_description,
        filter_2_description=filter_2_description,
        filters_are_identical=filters_are_identical,
    )


@router.get(
    path="/{campaign}/filter-options",
    response_model=FilterOptions,
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
async def read_filter_options(
    parameters: Annotated[
        CommonParametersCampaign, Depends(dependencies.dep_common_parameters_campaign)
    ]
):
    """Read filter options for campaign"""

    campaign_code = parameters.campaign_code
    language = parameters.language

    # Create service
    campaign_service = CampaignService(campaign_code=campaign_code, language=language)

    # Country options
    countries = campaign_service.get_countries_list()
    country_options = [
        Option(value=country.alpha2_code, label=country.name) for country in countries
    ]

    # Country regions options
    country_regions_options: list[dict[str, str | list[Option]]] = []
    for country in countries:
        regions_options = {"country_alpha2_code": country.alpha2_code, "options": []}
        for region in sorted(country.regions, key=lambda r: r.name):
            regions_options["options"].append(
                Option(value=region.code, label=region.name)
            )
        country_regions_options.append(regions_options)

    # Response topic options
    response_topics = campaign_service.get_response_topics()
    response_topic_options = [
        Option(
            value=response_topic.code,
            label=response_topic.name,
            metadata="is_parent" if response_topic.is_parent else "is_not_parent",
        )
        for response_topic in response_topics
    ]

    # Age options
    ages = campaign_service.get_ages()
    age_options = [Option(value=age.code, label=age.name) for age in ages]

    # Gender options
    genders = campaign_service.get_genders()
    gender_options = [
        Option(value=gender.code, label=gender.name) for gender in genders
    ]

    # Profession options
    professions = campaign_service.get_professions()
    profession_options = [
        Option(value=profession.code, label=profession.name)
        for profession in professions
    ]

    # Only responses from categories options
    only_responses_from_categories_options = (
        campaign_service.get_only_responses_from_categories_options()
    )

    # Only multi-word phrases containing filter term options
    only_multi_word_phrases_containing_filter_term_options = (
        campaign_service.get_only_multi_word_phrases_containing_filter_term_options()
    )

    # Translate
    try:
        if language != "en" and TranslationsCache().is_loaded():
            translator = Translator()
            translator.set_target_language(target_language=language)

            # Extract texts
            translator.apply_t_filter_options(
                t=translator.extract_text,
                country_options=country_options,
                country_regions_options=country_regions_options,
                response_topic_options=response_topic_options,
                age_options=age_options,
                gender_options=gender_options,
                profession_options=profession_options,
                only_responses_from_categories_options=only_responses_from_categories_options,
                only_multi_word_phrases_containing_filter_term_options=only_multi_word_phrases_containing_filter_term_options,
            )

            # Translate extracted texts
            translator.translate_extracted_texts()

            # Apply translations to texts
            (
                country_options,
                country_regions_options,
                response_topic_options,
                age_options,
                gender_options,
                profession_options,
                only_responses_from_categories_options,
                only_multi_word_phrases_containing_filter_term_options,
            ) = translator.apply_t_filter_options(
                t=translator.translate_text,
                country_options=country_options,
                country_regions_options=country_regions_options,
                response_topic_options=response_topic_options,
                age_options=age_options,
                gender_options=gender_options,
                profession_options=profession_options,
                only_responses_from_categories_options=only_responses_from_categories_options,
                only_multi_word_phrases_containing_filter_term_options=only_multi_word_phrases_containing_filter_term_options,
            )
    except (Exception,) as e:
        logger.warning(
            f"An error occurred during translation of 'filter_options': {str(e)}"
        )

    return FilterOptions(
        countries=country_options,
        country_regions=country_regions_options,
        response_topics=response_topic_options,
        ages=age_options,
        genders=gender_options,
        professions=profession_options,
        only_responses_from_categories=only_responses_from_categories_options,
        only_multi_word_phrases_containing_filter_term=only_multi_word_phrases_containing_filter_term_options,
    )


@router.get(
    path="/{campaign}/who-the-people-are-options",
    response_model=list[dict],
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
async def read_who_the_people_are_options(
    parameters: Annotated[
        CommonParametersCampaign, Depends(dependencies.dep_common_parameters_campaign)
    ]
):
    """Read who the people are options for campaign"""

    campaign_code = parameters.campaign_code
    language = parameters.language

    # Create service
    campaign_service = CampaignService(campaign_code=campaign_code, language=language)

    # Options
    options = campaign_service.get_who_the_people_are_options()

    # Translate
    try:
        if language != "en" and TranslationsCache().is_loaded():
            translator = Translator()
            translator.set_target_language(target_language=language)

            # Extract texts
            translator.apply_t_who_the_people_are_options(
                translator.extract_text, options=options
            )

            # Translate extracted texts
            translator.translate_extracted_texts()

            # Apply translations to texts
            options = translator.apply_t_who_the_people_are_options(
                translator.translate_text, options=options
            )
    except (Exception,) as e:
        logger.warning(
            f"An error occurred during translation of 'who_the_people_are_options': {str(e)}"
        )

    return options


@router.post(
    "/{campaign}/data",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
)
def campaign_data(
    parameters: Annotated[
        ParametersCampaignData,
        Depends(dependencies.dep_parameters_campaign_data),
    ]
):
    """Read campaign data"""

    campaign_code = parameters.campaign_code
    username = parameters.username
    from_date = parameters.from_date
    to_date = parameters.to_date

    # Cleanup
    cloud_storage_interactions.cleanup()

    # Get user
    users = databases.get_users()
    db_user = users.get(username)
    if not db_user:
        raise http_exceptions.UnauthorizedHTTPException("Unknown user")

    # Check if user has access to campaign
    if campaign_code not in db_user.campaign_access:
        raise http_exceptions.UnauthorizedHTTPException(
            "User has no access to campaign"
        )

    # CRUD
    crud = CampaignCRUD(campaign_code=campaign_code)

    # Get dataframe
    df = crud.get_dataframe()

    # File name
    csv_filename = f"wra_{campaign_code.value}.csv"

    # Filter by date
    date_format = "%Y_%m_%d"
    if from_date and to_date:
        df = df[
            (df["ingestion_time"].dt.date >= from_date)
            & (df["ingestion_time"].dt.date <= to_date)
        ]
        csv_filename = f"wra_{campaign_code.value}_{from_date.strftime(date_format)}_to_{to_date.strftime(date_format)}.csv"

    # File paths
    csv_filepath = f"/tmp/{csv_filename}"
    creating_csv_filepath = f"/tmp/wra_creating_{csv_filename}"
    cloud_storage_csv_filepath = f"{csv_filename}"

    # Raise exception if df has no data
    if len(df.index) < 1:
        raise http_exceptions.ResourceNotFoundHTTPException("No data found")

    # If file exists in Cloud Storage
    if cloud_storage_interactions.file_exists(filename=cloud_storage_csv_filepath):
        # Get storage url
        url = cloud_storage_interactions.get_file_url(
            filename=cloud_storage_csv_filepath
        )

    # If file does not exist in Cloud Storage
    else:
        if not os.path.isfile(csv_filepath):
            # Create '/tmp' dir (only if 'dev' because this dir already exists when in production if using App Engine)
            if os.getenv("STAGE") == "dev":
                if not os.path.isdir("/tmp"):
                    os.mkdir("/tmp")

            # Cleanup
            if os.path.isfile(creating_csv_filepath):
                os.remove(creating_csv_filepath)

            # Convert date to string
            df["ingestion_time"] = df["ingestion_time"].apply(
                lambda x: x.strftime(date_format) if x else ""
            )

            # Save dataframe to csv file
            df.to_csv(path_or_buf=creating_csv_filepath, index=False, header=True)

            # Rename
            os.rename(src=creating_csv_filepath, dst=csv_filepath)

        # Upload to storage
        cloud_storage_interactions.upload_file(
            source_filename=csv_filepath,
            destination_filename=cloud_storage_csv_filepath,
        )

        # Remove from tmp
        os.remove(csv_filepath)

        # Get storage url
        url = cloud_storage_interactions.get_file_url(
            filename=cloud_storage_csv_filepath
        )

    def iter_file():
        session = requests.Session()
        response = session.get(url=url, stream=True)

        if not response.ok:
            raise http_exceptions.ResourceNotFoundHTTPException("No data found")

        for chunk in response.iter_content(1024 * 1024):
            yield chunk

    return StreamingResponse(
        content=iter_file(),
        media_type="text/csv",
        headers={
            "Content-Type": "text/csv",
            f"Content-Disposition": f"attachment; filename={csv_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.get(
    "/{campaign}/countries-breakdown",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
)
async def campaign_countries_breakdown(
    campaign_code: Annotated[CampaignCode, Depends(dependencies.dep_campaign_code)],
    _: str = Depends(auth_handler.auth_wrapper_access_token),
):
    """Read campaign countries breakdown"""

    # CRUD
    crud = CampaignCRUD(campaign_code=campaign_code)

    # Get dataframe
    df = crud.get_dataframe()

    # Countries breakdown
    df = pd.DataFrame({"count": df.groupby(["canonical_country"]).size()}).reset_index()

    # Raise exception if df has no data
    if len(df.index) < 1:
        raise http_exceptions.ResourceNotFoundHTTPException("No data found")

    # Sort
    df = df.sort_values(by="count", ascending=False)

    # Rename column
    df = df.rename(columns={"canonical_country": "country"})

    # To csv
    buffer = StringIO()
    df.to_csv(path_or_buf=buffer, index=False, header=True)

    return StreamingResponse(
        content=iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Type": "text/csv",
            f"Content-Disposition": f"attachment; filename=wra_{campaign_code.value}_countries_breakdown.csv",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.get(
    "/{campaign}/source-files-breakdown",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
)
async def campaign_source_files_breakdown(
    campaign_code: Annotated[CampaignCode, Depends(dependencies.dep_campaign_code)],
    _: str = Depends(auth_handler.auth_wrapper_access_token),
):
    """Read campaign source files breakdown"""

    # CRUD
    crud = CampaignCRUD(campaign_code=campaign_code)

    # Get dataframe
    df = crud.get_dataframe()

    # Source files breakdown
    df = pd.DataFrame({"count": df.groupby(["data_source"]).size()}).reset_index()

    # Raise exception if df has no data
    if len(df.index) < 1:
        raise http_exceptions.ResourceNotFoundHTTPException("No data found")

    # Sort
    df = df.sort_values(by="count", ascending=False)

    # To csv
    buffer = StringIO()
    df.to_csv(path_or_buf=buffer, index=False, header=True)

    return StreamingResponse(
        content=iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Type": "text/csv",
            f"Content-Disposition": f"attachment; filename=wra_{campaign_code.value}_source_files_breakdown.csv",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
