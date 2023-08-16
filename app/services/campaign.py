"""
Handles processing of data and business logic for a campaign
"""

import operator
import random
import re
from collections import Counter
from typing import Callable

import pandas as pd

from app import constants, globals
from app.core.settings import settings
from app.crud.campaign import CampaignCRUD
from app.enums.campaign_code import CampaignCode
from app.enums.question_code import QuestionCode
from app.schemas.age import Age
from app.schemas.country import Country
from app.schemas.filter import Filter
from app.schemas.gender import Gender
from app.schemas.profession import Profession
from app.schemas.response_topic import ResponseTopic
from app.services import googlemaps_interactions
from app.services.translator import Translator
from app.utils import code_hierarchy
from app.utils import filters
from app.utils import helpers
from app.utils import q_col_names


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

        self.__translator = Translator()
        self.__translator.set_target_language(target_language=self.__language)
        self.__t = self.__translator.translate_text

        self.__crud = CampaignCRUD(campaign_code=self.__campaign_code)

        self.__filter_1 = filter_1
        self.__filter_2 = filter_2

        # Apply filter 1
        if self.__filter_1:
            self.__df_1 = filters.apply_filter_to_df(
                df=self.__crud.get_dataframe(),
                _filter=self.__filter_1,
                campaign_code=self.__campaign_code,
            )
        else:
            self.__df_1 = self.__crud.get_dataframe()

        # Apply filter 2
        if self.__filter_2:
            self.__df_2 = filters.apply_filter_to_df(
                df=self.__crud.get_dataframe(),
                _filter=self.__filter_2,
                campaign_code=self.__campaign_code,
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

        # Campaign question codes
        self.__campaign_q_codes = helpers.get_campaign_q_codes(
            campaign_code=campaign_code
        )

        # Ngrams
        self.__ngrams_1 = {}
        self.__ngrams_2 = {}
        for q_code in self.__campaign_q_codes:
            # Ngrams 1
            if self.__filter_1:
                self.__ngrams_1[q_code.value] = self.__get_ngrams_1(
                    only_multi_word_phrases_containing_filter_term=self.__filter_1.only_multi_word_phrases_containing_filter_term,
                    keyword=self.__filter_1.keyword_filter,
                    q_code=q_code,
                )
            else:
                self.__ngrams_1[q_code.value] = self.__get_ngrams_1(
                    only_multi_word_phrases_containing_filter_term=False,
                    keyword="",
                    q_code=q_code,
                )

            # Ngrams 2
            self.__ngrams_2[q_code.value] = self.__get_ngrams_2(q_code=q_code)

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

    def get_responses_sample(self, q_code: QuestionCode) -> list[dict]:
        """Get responses sample"""

        # Get copy to not modify original
        df_1_copy = self.__get_df_1_copy()

        response_sample_1 = self.__get_df_responses_sample(df=df_1_copy, q_code=q_code)

        # Only set responses_sample_2 if filter 2 was applied
        if self.__filter_2:
            # Get copy to not modify original
            df_2_copy = self.__get_df_2_copy()

            response_sample_2 = self.__get_df_responses_sample(
                df=df_2_copy, q_code=q_code
            )
        else:
            response_sample_2 = []

        responses_breakdown = response_sample_1 + response_sample_2

        # Shuffle
        random.shuffle(responses_breakdown)

        return responses_breakdown

    def __get_responses_sample_column_ids(self, q_code: QuestionCode = None) -> list:
        """Get responses column ids"""

        columns = self.__crud.get_responses_sample_columns()

        if not q_code:
            return [col["id"] for col in columns]

        # Rename column e.g. 'raw_response' -> 'q1_raw_response'
        for column in columns:
            if column.get("id") == "raw_response":
                column["id"] = f"{q_code.value}_raw_response"
            if column.get("id") == "description":
                column["id"] = f"{q_code.value}_description"

        return [col["id"] for col in columns]

    def __get_df_responses_sample(
        self, df: pd.DataFrame, q_code: QuestionCode
    ) -> list[dict]:
        """Get df responses sample"""

        # Set column names based on question code
        description_col_name = q_col_names.get_description_col_name(q_code=q_code)
        canonical_code_col_name = q_col_names.get_canonical_code_col_name(q_code=q_code)
        raw_response_col_name = q_col_names.get_raw_response_col_name(q_code=q_code)

        # Do not translate if this function is called while translating texts offline
        if settings.OFFLINE_TRANSLATE_MODE:
            return []

        # Limit the sample for languages that are not English
        if self.__language == "en":
            if self.__filter_2:
                n_sample = 500
            else:
                n_sample = 1000
        else:
            if self.__filter_2:
                n_sample = 50
            else:
                n_sample = 100

        if len(df.index) > 0:
            if len(df.index) < n_sample:
                n_sample = len(df.index)
            df_1_copy = df.sample(n=n_sample, random_state=1)
        else:
            return []

        column_ids = self.__get_responses_sample_column_ids(q_code=q_code)

        def get_descriptions(code: str, t: Callable) -> str:
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

            # Translate
            if t.__name__ == self.__translator.translate_text.__name__:
                descriptions = t(text=descriptions, delimiter=",")

            # Else extract
            else:
                descriptions = t(descriptions)

            return descriptions

        def translate_or_extract_responses_sample(t: Callable) -> pd.DataFrame:
            def translate_text_between_parentheses(text: str) -> str:
                """Find text between parentheses and translate it"""

                texts_between_parentheses = re.findall("\\(([^)]+)", text)
                if len(texts_between_parentheses) > 0:
                    text_between_parentheses = texts_between_parentheses[-1]
                    text = text.replace(
                        text_between_parentheses, t(text_between_parentheses)
                    )

                return text

            df_tmp = df_1_copy.copy()

            df_tmp[description_col_name] = df_tmp[canonical_code_col_name].apply(
                lambda x: get_descriptions(x, t)
            )

            # Translate column data
            for column_id in column_ids:
                # Skip 'description' as it is already translated
                if column_id == description_col_name:
                    continue

                # Do not translate age e.g. '25-34'
                if column_id == "age":
                    df_tmp[column_id] = df_tmp[column_id].apply(
                        lambda x: t(x) if helpers.contains_letters(x) else x
                    )

                if column_id == raw_response_col_name:
                    # economic_empowerment_mexico: Do not translate 'raw_response' if the language is 'es'
                    # economic_empowerment_mexico: For other languages, only translate text between parentheses
                    if self.__campaign_code == CampaignCode.economic_empowerment_mexico:
                        if self.__language != "es":
                            df_tmp[column_id] = df_tmp[column_id].apply(
                                translate_text_between_parentheses
                            )
                    else:
                        df_tmp[column_id] = df_tmp[column_id].apply(lambda x: t(x))

            return df_tmp

        # Only translate if language is not 'en'
        # Go through data initially to extract texts (to apply translations in chunks for faster results)
        # Translate the extracted texts
        # Go through data again to apply the translations on data
        if self.__language != "en":
            # Go through data and extract texts to be translated by sending the add_text_to_extract function
            translate_or_extract_responses_sample(self.__translator.add_text_to_extract)

            # Translate extracted texts
            self.__translator.translate_extracted_texts(skip_saving_to_json=True)

        # Go through data and apply translations of extracted texts by sending the translate_text function
        df_1_copy = translate_or_extract_responses_sample(self.__t)

        # Rename columns e.g. 'q1_raw_response' -> 'raw_response'
        columns_to_rename = {x: x.replace(f"{q_code.value}_", "") for x in column_ids}
        df_1_copy = df_1_copy.rename(columns=columns_to_rename)

        responses_sample_data = df_1_copy[columns_to_rename.values()].to_dict("records")

        return responses_sample_data

    def get_responses_breakdown(self, q_code: QuestionCode) -> list:
        """Get responses breakdown"""

        # Set column names based on question code
        canonical_code_col_name = q_col_names.get_canonical_code_col_name(q_code=q_code)
        label_col_name = q_col_names.get_label_col_name(q_code=q_code)
        count_col_name = q_col_names.get_count_col_name(q_code=q_code)
        code_col_name = q_col_names.get_code_col_name(q_code=q_code)
        description_col_name = q_col_names.get_description_col_name(q_code=q_code)

        def get_df_responses_breakdown(df: pd.DataFrame) -> list[dict]:
            """Get df responses breakdown"""

            # Count occurrence of responses
            counter = Counter()
            for canonical_code in df[canonical_code_col_name]:
                for c in canonical_code.split("/"):
                    counter[c] += 1

            if len(counter) > 0:
                # Create dataframe with items from counter
                df = pd.DataFrame(
                    sorted(counter.items(), key=operator.itemgetter(1), reverse=True)
                )

                # Set column names
                df.columns = [label_col_name, count_col_name]

                # Set code
                df[code_col_name] = df[label_col_name].map(
                    code_hierarchy.get_mapping_to_code(
                        campaign_code=self.__campaign_code
                    )
                )

                # Set description column
                df[description_col_name] = df[label_col_name].map(
                    code_hierarchy.get_mapping_to_description(
                        campaign_code=self.__campaign_code
                    )
                )

                # Translate descriptions
                df[description_col_name] = df[description_col_name].apply(
                    lambda x: self.__t(text=x, delimiter=",")
                )

                # Drop label column
                df = df.drop([label_col_name], axis=1)

                # Drop rows with nan values
                df = df.dropna()

                # what_young_people_want: Sort the rows by count value (DESC) and keep the first n rows only
                if self.__campaign_code == CampaignCode.what_young_people_want:
                    n_rows_keep = 5
                    df = df.sort_values(by=count_col_name, ascending=False)
                    df = df.head(n_rows_keep)
            else:
                df = pd.DataFrame()

            responses_breakdown_data = df.to_dict(orient="records")

            return responses_breakdown_data

        # Get copy to not modify original
        df_1_copy = self.__get_df_1_copy()
        df_2_copy = self.__get_df_2_copy()

        # Get responses breakdown from each df
        responses_breakdown_1 = get_df_responses_breakdown(df=df_1_copy)
        responses_breakdown_2 = get_df_responses_breakdown(df=df_2_copy)

        # Get all unique codes from responses breakdown
        codes_1 = [x[code_col_name] for x in responses_breakdown_1]
        codes_2 = [x[code_col_name] for x in responses_breakdown_2]
        all_codes = set(codes_1 + codes_2)

        # Responses breakdown
        responses_breakdown = []
        for code in all_codes:
            responses_1 = [x for x in responses_breakdown_1 if x[code_col_name] == code]
            responses_2 = [x for x in responses_breakdown_2 if x[code_col_name] == code]

            if responses_1:
                response_1 = responses_1[0]
            else:
                response_1 = None

            if responses_2:
                response_2 = responses_2[0]
            else:
                response_2 = None

            # Set description
            description = ""
            if response_1:
                description = response_1[description_col_name]
            if response_2:
                description = response_2[description_col_name]

            responses_breakdown.append(
                {
                    "count_1": response_1.get(count_col_name) if response_1 else 0,
                    "count_2": response_2.get(count_col_name) if response_2 else 0,
                    code_col_name.replace(f"{q_code.value}_", ""): code,
                    description_col_name.replace(f"{q_code.value}_", ""): description,
                }
            )

        # Sort responses breakdown
        responses_breakdown = sorted(
            responses_breakdown, key=lambda x: x["count_1"], reverse=True
        )

        return responses_breakdown

    def get_living_settings_breakdown(self) -> list:
        """Get living setting settings breakdown"""

        df_1_copy = self.__get_df_1_copy()
        df_2_copy = self.__get_df_2_copy()

        def fix_value(v: str):
            # If value in lower case is 'prefer not to say', then rename to 'Prefer not to say'
            if v.lower() == "prefer not to say":
                v = "Prefer not to say"

            return v

        df_1_copy["setting"] = df_1_copy["setting"].apply(fix_value)
        df_2_copy["setting"] = df_2_copy["setting"].apply(fix_value)

        # Get row count
        grouped_by_column_1 = df_1_copy.groupby("setting")["setting"].count()
        grouped_by_column_2 = df_2_copy.groupby("setting")["setting"].count()

        # Add count
        names = list(
            set(grouped_by_column_1.index.tolist() + grouped_by_column_2.index.tolist())
        )
        names = [name for name in names if name]

        living_settings_breakdown = []

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

            living_settings_breakdown.append(
                {
                    "name": self.__t(name) if helpers.contains_letters(name) else name,
                    "count_1": count_1,
                    "count_2": count_2,
                }
            )

        # Sort by count value (DESC)
        if not self.__filter_1 and not self.__filter_2:
            living_settings_breakdown = sorted(
                living_settings_breakdown,
                key=operator.itemgetter("count_1"),
                reverse=True,
            )
        elif self.__filter_1 and not self.__filter_2:
            living_settings_breakdown = sorted(
                living_settings_breakdown,
                key=operator.itemgetter("count_2"),
                reverse=True,
            )
        elif not self.__filter_1 and self.__filter_2:
            living_settings_breakdown = sorted(
                living_settings_breakdown,
                key=operator.itemgetter("count_1"),
                reverse=True,
            )

        return living_settings_breakdown

    def get_wordcloud_words(self, q_code: QuestionCode) -> list[dict]:
        """Get wordcloud words"""

        (
            unigram_count_dict,
            bigram_count_dict,
            trigram_count_dict,
        ) = self.__ngrams_1[q_code.value]

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

    def get_top_words(self, q_code: QuestionCode) -> list:
        """Get top words"""

        # Set unigram count dict based on question code
        if q_code == QuestionCode.q2:
            unigram_count_dict_1 = self.__ngrams_1[q_code.value][0]
            unigram_count_dict_2 = self.__ngrams_2[q_code.value][0]
        else:
            unigram_count_dict_1 = self.__ngrams_1[q_code.value][0]
            unigram_count_dict_2 = self.__ngrams_2[q_code.value][0]

        top_words = self.__get_ngram_top_words_or_phrases(
            ngram_count_dict_1=unigram_count_dict_1,
            ngram_count_dict_2=unigram_count_dict_2,
        )

        return top_words

    def get_two_word_phrases(self, q_code: QuestionCode) -> list:
        """Get two word phrases"""

        bigram_count_dict_1 = self.__ngrams_1[q_code.value][1]
        bigram_count_dict_2 = self.__ngrams_2[q_code.value][1]

        top_words = self.__get_ngram_top_words_or_phrases(
            ngram_count_dict_1=bigram_count_dict_1,
            ngram_count_dict_2=bigram_count_dict_2,
        )

        return top_words

    def get_three_word_phrases(self, q_code: QuestionCode) -> list:
        """Get three word phrases"""

        trigram_count_dict_1 = self.__ngrams_1[q_code.value][2]
        trigram_count_dict_2 = self.__ngrams_2[q_code.value][2]

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

    def generate_ngrams(
        self,
        df: pd.DataFrame,
        q_code: QuestionCode,
        only_multi_word_phrases_containing_filter_term: bool = False,
        keyword: str = "",
    ):
        """Generate ngrams"""

        # Set column name based on question code
        tokenized_column_name = q_col_names.get_tokenized_col_name(q_code=q_code)

        # Stopwords
        all_stopwords = constants.STOPWORDS
        if self.__language in all_stopwords:
            stopwords = set(all_stopwords.get(self.__language))
        else:
            stopwords = set()

        extra_stopwords = self.__crud.get_extra_stopwords()
        stopwords = stopwords.union(extra_stopwords)

        # ngram counters
        unigram_count_dict = Counter()
        bigram_count_dict = Counter()
        trigram_count_dict = Counter()

        for words_list in df[tokenized_column_name]:
            # Unigram
            for i in range(len(words_list)):
                if words_list[i] not in stopwords:
                    unigram_count_dict[words_list[i]] += 1

            # Bigram
            for i in range(len(words_list) - 1):
                if (
                    words_list[i] not in stopwords
                    and words_list[i + 1] not in stopwords
                ):
                    word_pair = f"{words_list[i]} {words_list[i + 1]}"
                    bigram_count_dict[word_pair] += 1

            # Trigram
            for i in range(len(words_list) - 2):
                if (
                    words_list[i] not in stopwords
                    and words_list[i + 1] not in stopwords
                    and words_list[i + 2] not in stopwords
                ):
                    word_trio = (
                        f"{words_list[i]} {words_list[i + 1]} {words_list[i + 2]}"
                    )
                    trigram_count_dict[word_trio] += 1

        unigram_count_dict = dict(unigram_count_dict)
        bigram_count_dict = dict(bigram_count_dict)
        trigram_count_dict = dict(trigram_count_dict)

        # Only show words in bigram and trigram if it contains the keyword
        if only_multi_word_phrases_containing_filter_term and len(keyword) > 0:
            bigram_count_dict = dict(
                (a, b) for a, b in bigram_count_dict.items() if keyword in a
            )
            trigram_count_dict = dict(
                (a, b) for a, b in trigram_count_dict.items() if keyword in a
            )

        return unigram_count_dict, bigram_count_dict, trigram_count_dict

    def __get_ngrams_1(
        self,
        only_multi_word_phrases_containing_filter_term: bool,
        keyword: str,
        q_code: QuestionCode,
    ) -> tuple:
        """Get ngrams 1"""

        # Return the cached ngrams (this is when filter 1 was not requested)
        if self.__filter_1_use_ngrams_unfiltered:
            return self.__crud.get_ngrams_unfiltered(q_code=q_code)

        (
            unigram_count_dict,
            bigram_count_dict,
            trigram_count_dict,
        ) = self.generate_ngrams(
            df=self.__get_df_1_copy(),
            only_multi_word_phrases_containing_filter_term=only_multi_word_phrases_containing_filter_term,
            keyword=keyword,
            q_code=q_code,
        )

        return unigram_count_dict, bigram_count_dict, trigram_count_dict

    def __get_ngrams_2(self, q_code: QuestionCode) -> tuple:
        """Get ngrams 2"""

        # Return the cached ngrams (this is when filter 2 was not requested)
        if self.__filter_2_use_ngrams_unfiltered:
            return self.__crud.get_ngrams_unfiltered(q_code=q_code)

        (
            unigram_count_dict,
            bigram_count_dict,
            trigram_count_dict,
        ) = self.generate_ngrams(df=self.__get_df_2_copy(), q_code=q_code)

        return unigram_count_dict, bigram_count_dict, trigram_count_dict

    def get_histogram(self) -> dict:
        """Get histogram"""

        df_1_copy = self.__get_df_1_copy()
        df_2_copy = self.__get_df_2_copy()

        # Get histogram for the keys used in the dictionary below
        histogram = {"age": [], "gender": [], "profession": [], "canonical_country": []}

        for column_name in list(histogram.keys()):
            # For each unique column value, get its row count
            grouped_by_column_1 = df_1_copy.groupby(column_name)[
                "q1_raw_response"
            ].count()
            grouped_by_column_2 = df_2_copy.groupby(column_name)[
                "q1_raw_response"
            ].count()

            # Add count for each unique column value
            names = list(
                set(
                    grouped_by_column_1.index.tolist()
                    + grouped_by_column_2.index.tolist()
                )
            )
            names = [name for name in names if name]

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
        elif self.__campaign_code == CampaignCode.what_young_people_want:
            options = [breakdown_age_option, breakdown_gender, breakdown_country_option]
        elif self.__campaign_code == CampaignCode.midwives_voices:
            options = [
                breakdown_age_option,
                breakdown_profession,
                breakdown_country_option,
            ]
        elif self.__campaign_code == CampaignCode.healthwellbeing:
            options = [breakdown_age_option, breakdown_country_option]
        elif self.__campaign_code == CampaignCode.economic_empowerment_mexico:
            options = [breakdown_age_option]
        elif self.__campaign_code == CampaignCode.what_women_want_pakistan:
            options = [breakdown_age_option]

        return options

    def get_genders_breakdown(self) -> list[dict]:
        """Get genders breakdown"""

        df_1_copy = self.__get_df_1_copy()

        gender_counts = df_1_copy["gender"].value_counts(ascending=True).to_dict()

        genders_breakdown = []
        for key, value in gender_counts.items():
            if not key:
                continue

            genders_breakdown.append({"name": self.__t(key), "count": value})

        return genders_breakdown

    def get_world_bubble_maps_coordinates(self) -> dict:
        """Get world bubble maps coordinates"""

        def get_country_coordinates(alpha2country_counts: dict):
            """Add coordinate and count for each country"""

            country_coordinates = []
            for key, value in alpha2country_counts.items():
                lat = constants.COUNTRY_COORDINATE.get(key)[0]
                lon = constants.COUNTRY_COORDINATE.get(key)[1]
                country_name = constants.COUNTRIES_DATA.get(key).get("name")

                if not lat or not lon or not country_name:
                    continue

                country_coordinates.append(
                    {
                        "location_code": key,
                        "location_name": self.__t(country_name),
                        "n": value,
                        "lat": lat,
                        "lon": lon,
                    }
                )

            return country_coordinates

        def get_region_coordinates(region_counts: dict):
            """Add coordinate and count for each region"""

            region_coordinates = []

            for (
                alpha2country,
                canonical_country,
                region,
            ), value in region_counts.items():
                # TODO: Why is there an empty region?
                if not region:
                    continue

                country_regions_coordinates = globals.coordinates.get(alpha2country)

                # Check if the region's coordinate already exists
                coordinate_found = False
                if country_regions_coordinates and country_regions_coordinates.get(
                    region
                ):
                    coordinate_found = True

                # Get coordinate from googlemaps if it was not found
                if not coordinate_found:
                    coordinate = googlemaps_interactions.get_coordinate(
                        location=f"{canonical_country}, {region}"
                    )
                    if not coordinate:
                        continue

                    # Add the new coordinate
                    if not globals.coordinates.get(alpha2country):
                        globals.coordinates[alpha2country] = {}
                    globals.coordinates[alpha2country][region] = coordinate

                # Create region_coordinates
                lat = globals.coordinates[alpha2country][region].get("lat")
                lon = globals.coordinates[alpha2country][region].get("lon")
                region_coordinates.append(
                    {
                        "location_code": region,
                        "location_name": region,
                        "n": value,
                        "lat": lat,
                        "lon": lon,
                    }
                )

            return region_coordinates

        # Get copy to not modify original
        df_1_copy = self.__get_df_1_copy()
        df_2_copy = self.__get_df_2_copy()

        # For these campaigns, use region as location
        if (
            self.__campaign_code == CampaignCode.economic_empowerment_mexico
            or self.__campaign_code == CampaignCode.what_women_want_pakistan
        ):
            # Get count of each region per country
            region_counts_1 = (
                df_1_copy[["alpha2country", "canonical_country", "region"]]
                .value_counts(ascending=True)
                .to_dict()
            )
            coordinates_1 = get_region_coordinates(region_counts=region_counts_1)

            # Get count of each region per country
            region_counts_2 = (
                df_2_copy[["alpha2country", "canonical_country", "region"]]
                .value_counts(ascending=True)
                .to_dict()
            )
            coordinates_2 = get_region_coordinates(region_counts=region_counts_2)

            coordinates = {
                "coordinates_1": coordinates_1,
                "coordinates_2": coordinates_2,
            }

        # For other campaigns, use country as location
        else:
            # Get count of each country
            alpha2country_counts_1 = (
                df_1_copy["alpha2country"].value_counts(ascending=True).to_dict()
            )
            coordinates_1 = get_country_coordinates(
                alpha2country_counts=alpha2country_counts_1
            )

            # Get count of each country
            alpha2country_counts_2 = (
                df_2_copy["alpha2country"].value_counts(ascending=True).to_dict()
            )
            coordinates_2 = get_country_coordinates(
                alpha2country_counts=alpha2country_counts_2
            )

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

        # Sort countries
        countries = sorted(countries, key=lambda x: x.name)

        return countries

    def get_ages(self) -> list[Age]:
        """Get ages"""

        def convert_numeric(age_str: str):
            return age_str.zfill(6)  # zero-pad the age string

        ages = self.__crud.get_ages()

        # Translate
        for index, age in enumerate(ages):
            age.name = (
                self.__t(age.name) if helpers.contains_letters(age.name) else age.name
            )

        # Sort ages
        ages = sorted(ages, key=lambda a: convert_numeric(a.name))

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
