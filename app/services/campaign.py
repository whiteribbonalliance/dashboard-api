"""
Handles processing of data and business logic for a campaign
"""

import operator
from collections import Counter

import pandas as pd

from app import constants
from app.crud.campaign import CampaignCRUD
from app.enums.campaign_code import CampaignCode
from app.schemas.age import Age
from app.schemas.country import Country
from app.schemas.filter import Filter
from app.schemas.gender import Gender
from app.schemas.profession import Profession
from app.schemas.response_topic import ResponseTopic
from app.services.translator import Translator
from app.utils import code_hierarchy
from app.utils import filters
from app.utils import helpers


class CampaignService:
    def __init__(
        self,
        campaign_code: CampaignCode,
        language: str = "en",
        filter_1: Filter | None = None,
        filter_2: Filter | None = None,
    ):
        self.__campaign_code = campaign_code
        self.__language = language

        translator = Translator.get_instance()
        translator.set_language(language=self.__language)
        self.__t = translator.translate_text

        self.__crud = CampaignCRUD(campaign_code=self.__campaign_code)

        self.__filter_1 = filter_1
        self.__filter_2 = filter_2

        # Apply filter 1
        if self.__filter_1:
            self.__df_1 = filters.apply_filter_to_df(
                df=self.__crud.get_dataframe(), _filter=self.__filter_1
            )
        else:
            self.__df_1 = self.__crud.get_dataframe()

        # Apply filter 2
        if self.__filter_2:
            self.__df_2 = filters.apply_filter_to_df(
                df=self.__crud.get_dataframe(), _filter=self.__filter_2
            )
        else:
            self.__df_2 = self.__crud.get_dataframe()

        # Filter 1 description
        self.__filter_1_description = self.__get_filter_description(
            df=self.__df_1, _filter=self.__filter_1
        )

        # Filter 2 description
        self.__filter_2_description = self.__get_filter_description(
            df=self.__df_2, _filter=self.__filter_2
        )

        # If filter 1 was requested, then do not use the cached ngrams
        self.__filter_1_use_ngrams_unfiltered = True
        if self.__filter_1 and not filters.check_if_filter_is_default(
            _filter=self.__filter_1
        ):
            self.__filter_1_use_ngrams_unfiltered = False

        # If filter 2 was requested, then do not use the cached ngrams
        self.__filter_2_use_ngrams_unfiltered = True
        if self.__filter_2 and not filters.check_if_filter_is_default(
            _filter=self.__filter_2
        ):
            self.__filter_2_use_ngrams_unfiltered = False

        # Ngrams 1
        self.__ngrams_1 = self.__get_ngrams_1()

        # Ngrams 2
        self.__ngrams_2 = self.__get_ngrams_2()

        # Check if filters are identical or not
        self.filters_are_identical = filters.check_if_filters_are_identical(
            filter_1=filter_1, filter_2=filter_2
        )

    def get_responses_sample_columns(self) -> list[dict]:
        """Get responses sample columns"""

        responses_sample_columns = self.__crud.get_responses_sample_columns()

        # Translate column names
        for column in responses_sample_columns:
            if not column.get("name"):
                continue

            column["name"] = self.__t(column["name"])

        return responses_sample_columns

    def get_responses_sample(self) -> list[dict]:
        """Get responses sample"""

        def get_descriptions(code: str) -> str:
            """Get descriptions"""

            mapping_to_description = code_hierarchy.get_mapping_to_description(
                campaign_code=self.__campaign_code
            )

            descriptions = mapping_to_description.get(
                code,
                " / ".join(
                    sorted(
                        set([mapping_to_description.get(x, x) for x in code.split("/")])
                    )
                ),
            )

            # Translate descriptions
            descriptions = self.__t(text=descriptions, delimiter=",")

            return descriptions

        # Get copy to not modify original
        df_1_copy = self.__get_df_1_copy()

        # Limit the sample for languages that are not English
        if self.__language == "en":
            n_sample = 1000
        else:
            n_sample = 100

        if len(df_1_copy.index) > 0:
            if len(df_1_copy.index) < n_sample:
                n_sample = len(df_1_copy.index)
            df_1_copy = df_1_copy.sample(n=n_sample, random_state=1)

        df_1_copy["description"] = df_1_copy["canonical_code"].apply(get_descriptions)

        column_ids = [col["id"] for col in self.__crud.get_responses_sample_columns()]

        # Translate column data
        for column_id in column_ids:
            # Skip 'descriptions' as it is already translated
            if column_id == "description":
                continue

            if column_id == "age":
                # Do not translate age e.g. '25-34'
                df_1_copy[column_id] = df_1_copy[column_id].apply(
                    lambda x: self.__t(x) if helpers.contains_letters(x) else x
                )
            else:
                df_1_copy[column_id] = df_1_copy[column_id].apply(lambda x: self.__t(x))

        responses_sample_data = df_1_copy[column_ids].to_dict("records")

        return responses_sample_data

    def get_responses_breakdown(self) -> list[dict]:
        """Get responses breakdown"""

        # Get copy to not modify original
        df_1_copy = self.__get_df_1_copy()

        # Count occurrence of responses
        counter = Counter()
        for canonical_code in df_1_copy["canonical_code"]:
            for code in canonical_code.split("/"):
                counter[code] += 1

        if len(counter) > 0:
            # Create dataframe with items from counter
            df = pd.DataFrame(
                sorted(counter.items(), key=operator.itemgetter(1), reverse=True)
            )

            # Set column names
            df.columns = ["label", "count"]

            # Set description column
            df["description"] = df["label"].map(
                code_hierarchy.get_mapping_to_description(
                    campaign_code=self.__campaign_code
                )
            )

            # Translate descriptions
            df["description"] = df["description"].apply(
                lambda description: self.__t(text=description, delimiter=",")
            )

            # Set top level column
            # df["top_level"] = df["label"].map(
            #     code_hierarchy.get_mapping_to_top_level(campaign_code=self.__campaign_code))

            # Drop label column
            df = df.drop(["label"], axis=1)

            # Drop rows with nan values
            df = df.dropna()

            # PMNCH: Sort the rows by count value (DESC) and keep the first n rows only
            if self.__campaign_code == CampaignCode.what_young_people_want:
                n_rows_keep = 5
                df = df.sort_values(by="count", ascending=False)
                df = df.head(n_rows_keep)
        else:
            df = pd.DataFrame()

        responses_breakdown_data = df.to_dict(orient="records")

        return responses_breakdown_data

    def get_wordcloud_words(self) -> list[dict]:
        """Get wordcloud words"""

        unigram_count_dict, bigram_count_dict, trigram_count_dict = self.__ngrams_1

        # Get words for wordcloud
        wordcloud_words = (
            unigram_count_dict
            | dict([(k, v) for k, v in bigram_count_dict.items()])
            | dict([(k, v) for k, v in trigram_count_dict.items()])
        )

        # Sort the words
        wordcloud_words = sorted(
            wordcloud_words.items(), key=lambda x: x[1], reverse=True
        )

        # Only keep the first 100 words
        n_words_to_keep = 100
        wordcloud_words_length = len(wordcloud_words)
        if wordcloud_words_length < n_words_to_keep:
            n_words_to_keep = wordcloud_words_length
        wordcloud_words = wordcloud_words[:n_words_to_keep]

        wordcloud_words_list = [
            {"text": self.__t(key), "value": item}
            for key, item in dict(wordcloud_words).items()
        ]

        return wordcloud_words_list

    def get_top_words(self) -> list:
        """Get top words"""

        unigram_count_dict_1 = self.__ngrams_1[0]
        unigram_count_dict_2 = self.__ngrams_2[0]

        top_words = self.__get_ngram_top_words_or_phrases(
            ngram_count_dict_1=unigram_count_dict_1,
            ngram_count_dict_2=unigram_count_dict_2,
        )

        return top_words

    def get_two_word_phrases(self) -> list:
        """Get two word phrases"""

        bigram_count_dict_1 = self.__ngrams_1[1]
        bigram_count_dict_2 = self.__ngrams_2[1]

        top_words = self.__get_ngram_top_words_or_phrases(
            ngram_count_dict_1=bigram_count_dict_1,
            ngram_count_dict_2=bigram_count_dict_2,
        )

        return top_words

    def get_three_word_phrases(self) -> list:
        """Get three word phrases"""

        trigram_count_dict_1 = self.__ngrams_1[2]
        trigram_count_dict_2 = self.__ngrams_2[2]

        top_words = self.__get_ngram_top_words_or_phrases(
            ngram_count_dict_1=trigram_count_dict_1,
            ngram_count_dict_2=trigram_count_dict_2,
        )

        return top_words

    def __get_ngram_top_words_or_phrases(
        self, ngram_count_dict_1: dict, ngram_count_dict_2: dict
    ) -> list:
        """Get ngram top words/phrases"""

        if len(ngram_count_dict_1) == 0:
            return []

        unigram_count_dict_1 = sorted(
            ngram_count_dict_1.items(), key=operator.itemgetter(1)
        )
        max1 = 0

        if len(unigram_count_dict_1) > 0:
            max1 = unigram_count_dict_1[-1][1]

        if len(unigram_count_dict_1) > 20:
            unigram_count_dict_1 = unigram_count_dict_1[-20:]

        # words list + top words 1 frequency
        if len(unigram_count_dict_1) == 0:
            word_list, freq_list_top_1 = [], []
        else:
            word_list, freq_list_top_1 = zip(*unigram_count_dict_1)
        if (
            len(ngram_count_dict_2) > 0
            and len(unigram_count_dict_1) > 0
            and len(freq_list_top_1) > 0
        ):
            max2 = max(ngram_count_dict_2.values())
            normalisation_factor = max1 / max2
        else:
            normalisation_factor = 1

        # Top words 2 frequency
        freq_list_top_2 = [
            int(ngram_count_dict_2.get(w, 0) * normalisation_factor) for w in word_list
        ]

        top_words = [
            {
                "word": self.__t(text=word, delimiter=" "),
                "count_1": freq_list_top_1[(len(word_list) - 1) - index],
                "count_2": freq_list_top_2[(len(word_list) - 1) - index],
            }
            for index, word in enumerate(reversed(word_list))
        ]

        return top_words

    def get_response_topics(self) -> list[ResponseTopic]:
        """Get response topics"""

        hierarchy = self.__crud.get_category_hierarchy()
        response_topics = []
        for top_level, leaves in hierarchy.items():
            for code, name in leaves.items():
                response_topics.append(ResponseTopic(code=code, name=self.__t(name)))

        return response_topics

    def __get_df_1_copy(self) -> pd.DataFrame:
        """Get dataframe 1 copy"""

        return self.__df_1.copy()

    def __get_df_2_copy(self) -> pd.DataFrame:
        """Get dataframe 2 copy"""

        return self.__df_2.copy()

    def get_filter_1_description(self) -> str:
        """Get filter 1 description"""

        return self.__t(self.__filter_1_description)

    def get_filter_2_description(self) -> str:
        """Get filter 2 description"""

        return self.__t(self.__filter_2_description)

    def __get_filter_description(self, df: pd.DataFrame, _filter: Filter) -> str:
        """Get filter description"""

        if not _filter:
            # Use an empty filter to generate description
            _filter = filters.get_default_filter()

        description = filters.generate_description_of_filter(
            campaign_code=self.__campaign_code,
            _filter=_filter,
            num_results=len(df),
            respondent_noun_singular=self.__crud.get_respondent_noun_singular(),
            respondent_noun_plural=self.__crud.get_respondent_noun_plural(),
        )

        return description

    def get_filter_1_respondents_count(self) -> int:
        """Get filter 1 respondents count"""

        return len(self.__df_1.index)

    def get_filter_2_respondents_count(self) -> int:
        """Get filter 2 respondents count"""

        return len(self.__df_2.index)

    def get_filter_1_average_age(self) -> str:
        """Get filter 1 average age"""

        df_1_copy = self.__get_df_1_copy()

        average_age = "N/A"
        if len(df_1_copy.index) > 0:  #
            average_age = " ".join(df_1_copy["age"].mode())
            average_age = (
                self.__t(average_age)
                if helpers.contains_letters(average_age)
                else average_age
            )

        return average_age

    def get_filter_2_average_age(self) -> str:
        """Get filter 2 average age"""

        df_2_copy = self.__get_df_2_copy()

        average_age = "N/A"
        if len(df_2_copy.index) > 0:  #
            average_age = " ".join(df_2_copy["age"].mode())

        return average_age

    def generate_ngrams(self, df: pd.DataFrame):
        """Generate ngrams"""

        # Stopwords
        extra_stopwords = self.__crud.get_extra_stopwords()
        all_stopwords = constants.STOPWORDS.union(extra_stopwords)

        # ngram counters
        unigram_count_dict = Counter()
        bigram_count_dict = Counter()
        trigram_count_dict = Counter()

        for words_list in df["tokenized"]:
            # Unigram
            for i in range(len(words_list)):
                if words_list[i] not in all_stopwords:
                    unigram_count_dict[words_list[i]] += 1

            # Bigram
            for i in range(len(words_list) - 1):
                if (
                    words_list[i] not in all_stopwords
                    and words_list[i + 1] not in all_stopwords
                ):
                    word_pair = f"{words_list[i]} {words_list[i + 1]}"
                    bigram_count_dict[word_pair] += 1

            # Trigram
            for i in range(len(words_list) - 2):
                if (
                    words_list[i] not in all_stopwords
                    and words_list[i + 1] not in all_stopwords
                    and words_list[i + 2] not in all_stopwords
                ):
                    word_trio = (
                        f"{words_list[i]} {words_list[i + 1]} {words_list[i + 2]}"
                    )
                    trigram_count_dict[word_trio] += 1

        unigram_count_dict = dict(unigram_count_dict)
        bigram_count_dict = dict(bigram_count_dict)
        trigram_count_dict = dict(trigram_count_dict)

        return unigram_count_dict, bigram_count_dict, trigram_count_dict

    def __get_ngrams_1(self) -> tuple:
        """Get ngrams 1"""

        # Return the cached ngrams (this is when filter 1 was not requested)
        if self.__filter_1_use_ngrams_unfiltered:
            (
                unigram_count_dict,
                bigram_count_dict,
                trigram_count_dict,
            ) = self.__crud.get_ngrams_unfiltered()

            return unigram_count_dict, bigram_count_dict, trigram_count_dict

        (
            unigram_count_dict,
            bigram_count_dict,
            trigram_count_dict,
        ) = self.generate_ngrams(df=self.__get_df_1_copy())

        return unigram_count_dict, bigram_count_dict, trigram_count_dict

    def __get_ngrams_2(self) -> tuple:
        """Get ngrams 2"""

        # Return the cached ngrams (this is when filter 2 was not requested)
        if self.__filter_2_use_ngrams_unfiltered:
            (
                unigram_count_dict,
                bigram_count_dict,
                trigram_count_dict,
            ) = self.__crud.get_ngrams_unfiltered()

            return unigram_count_dict, bigram_count_dict, trigram_count_dict

        (
            unigram_count_dict,
            bigram_count_dict,
            trigram_count_dict,
        ) = self.generate_ngrams(df=self.__get_df_2_copy())

        return unigram_count_dict, bigram_count_dict, trigram_count_dict

    def get_histogram(self) -> dict:
        """Get histogram"""

        df_1_copy = self.__get_df_1_copy()
        df_2_copy = self.__get_df_2_copy()

        # Get histogram for the keys used in the dictionary below
        histogram = {"age": [], "gender": [], "profession": [], "canonical_country": []}

        for column_name in list(histogram.keys()):
            # For each unique column value, get its row count
            grouped_by_column_1 = df_1_copy.groupby(column_name)["raw_response"].count()
            grouped_by_column_2 = df_2_copy.groupby(column_name)["raw_response"].count()

            # Add count for each unique column value
            names = list(
                set(
                    grouped_by_column_1.index.tolist()
                    + grouped_by_column_2.index.tolist()
                )
            )

            # Sort ages (values with ages first reverse sorted, then add other values back in e.g. 'prefer not to say')
            if column_name == "age" and len(names) > 0:
                names.sort(reverse=True)
                tmp_names = []
                tmp_names_not_ages = []
                for name in names:
                    try:
                        if not name[0].isnumeric():
                            tmp_names_not_ages.append(name)
                        else:
                            tmp_names.append(name)
                    except KeyError:
                        continue
                names = tmp_names + tmp_names_not_ages

            # Set count values
            for name in names:
                try:
                    count_1 = grouped_by_column_1[name].item()
                except KeyError:
                    count_1 = 0
                try:
                    count_2 = grouped_by_column_2[name].item()
                except KeyError:
                    count_2 = 0

                histogram[column_name].append(
                    {
                        "name": self.__t(name)
                        if helpers.contains_letters(name)
                        else name,
                        "count_1": count_1,
                        "count_2": count_2,
                    }
                )

            # Sort the columns below by count value (ASC)
            if (
                column_name == "canonical_country"
                or column_name == "profession"
                or column_name == "gender"
            ):
                if not self.__filter_1 and not self.__filter_2:
                    histogram[column_name] = sorted(
                        histogram[column_name], key=operator.itemgetter("count_1")
                    )
                elif self.__filter_1 and not self.__filter_2:
                    histogram[column_name] = sorted(
                        histogram[column_name], key=operator.itemgetter("count_2")
                    )
                elif not self.__filter_1 and self.__filter_2:
                    histogram[column_name] = sorted(
                        histogram[column_name], key=operator.itemgetter("count_1")
                    )

            # Limit to last 20 results
            if column_name == "canonical_country" or column_name == "profession":
                keep_last_n = 20
                if len(histogram[column_name]) > keep_last_n:
                    histogram[column_name] = histogram[column_name][-keep_last_n:]

        return histogram

    def get_who_the_people_are_options(self) -> list[dict]:
        """Get who the people are options"""

        breakdown_country_option = {
            "value": "breakdown-country",
            "label": f"{self.__t('Show breakdown by country')}",
        }
        breakdown_age_option = {
            "value": "breakdown-age",
            "label": f"{self.__t('Show breakdown by age')}",
        }
        breakdown_gender = {
            "value": "breakdown-gender",
            "label": f"{self.__t('Show breakdown by gender')}",
        }
        breakdown_profession = {
            "value": "breakdown-profession",
            "label": f"{self.__t('Show breakdown by profession')}",
        }

        options = []

        if self.__campaign_code == CampaignCode.what_women_want:
            options = [breakdown_age_option, breakdown_country_option]
        if self.__campaign_code == CampaignCode.what_young_people_want:
            options = [breakdown_age_option, breakdown_gender, breakdown_country_option]
        if self.__campaign_code == CampaignCode.midwives_voices:
            options = [
                breakdown_age_option,
                breakdown_profession,
                breakdown_country_option,
            ]

        return options

    def get_genders_breakdown(self) -> list[dict]:
        """Get genders breakdown"""

        df_1_copy = self.__get_df_1_copy()

        gender_counts = df_1_copy["gender"].value_counts(ascending=True).to_dict()

        genders_breakdown = []
        for key, value in gender_counts.items():
            genders_breakdown.append({"name": self.__t(key), "count": value})

        return genders_breakdown

    def get_world_bubble_maps_coordinates(self) -> dict:
        """Get world bubble maps coordinates"""

        def get_coordinates(alpha2country_counts):
            """Add coordinate and count for each country"""

            _coordinates = []
            for key, value in alpha2country_counts.items():
                lat = constants.COUNTRY_COORDINATE.get(key)[0]
                lon = constants.COUNTRY_COORDINATE.get(key)[1]
                country_name = constants.COUNTRIES_DATA.get(key).get("name")

                if not lat or not lon or not country_name:
                    continue

                _coordinates.append(
                    {
                        "country_alpha2_code": key,
                        "country_name": self.__t(country_name),
                        "n": value,
                        "lat": lat,
                        "lon": lon,
                    }
                )

            return _coordinates

        # Get copy to not modify original
        df_1_copy = self.__get_df_1_copy()
        df_2_copy = self.__get_df_2_copy()

        # Get count of each country
        alpha2country_counts_1 = (
            df_1_copy["alpha2country"].value_counts(ascending=True).to_dict()
        )
        coordinates_1 = get_coordinates(alpha2country_counts=alpha2country_counts_1)

        # Get count of each country
        alpha2country_counts_2 = (
            df_2_copy["alpha2country"].value_counts(ascending=True).to_dict()
        )
        coordinates_2 = get_coordinates(alpha2country_counts=alpha2country_counts_2)

        coordinates = {
            "coordinates_1": coordinates_1,
            "coordinates_2": coordinates_2,
        }

        return coordinates

    def get_filters_are_identical(self) -> bool:
        """Get filters are identical"""

        return self.filters_are_identical

    def get_countries_list(self) -> list[Country]:
        """Get countries list"""

        countries = self.__crud.get_countries_list()

        # Translate
        for country in countries:
            country.name = self.__t(country.name)
            country.demonym = self.__t(country.demonym)

            for region in country.regions:
                region.name = self.__t(region.name)

        return countries

    def get_ages(self) -> list[Age]:
        """Get ages"""

        ages = self.__crud.get_ages()

        # Translate
        for index, age in enumerate(ages):
            age.name = (
                self.__t(age.name) if helpers.contains_letters(age.name) else age.name
            )

        return ages

    def get_genders(self) -> list[Gender]:
        """Get genders"""

        genders = self.__crud.get_genders()

        # Translate
        for index, gender in enumerate(genders):
            gender.name = self.__t(gender.name)

        return genders

    def get_professions(self) -> list[Profession]:
        """Get professions"""

        professions = self.__crud.get_professions()

        # Translate
        for index, profession in enumerate(professions):
            profession.name = self.__t(profession.name)

        return professions

    def get_only_responses_from_categories_options(self) -> list[dict]:
        """Get only responses from categories options"""

        only_responses_from_categories_options = (
            self.__crud.get_only_responses_from_categories_options()
        )

        # Translate
        for option in only_responses_from_categories_options:
            option["label"] = self.__t(option["label"])

        return only_responses_from_categories_options

    def get_only_multi_word_phrases_containing_filter_term_options(self) -> list[dict]:
        """Get only multi-word phrases containing filter term options"""

        only_multi_word_phrases_containing_filter_term_options = (
            self.__crud.get_only_multi_word_phrases_containing_filter_term_options()
        )

        # Translate
        for option in only_multi_word_phrases_containing_filter_term_options:
            option["label"] = self.__t(option["label"])

        return only_multi_word_phrases_containing_filter_term_options
