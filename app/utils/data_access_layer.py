"""
Reads data from a databank
"""

import operator
from collections import Counter

import inflect
import pandas as pd

from app import databank
from app.enums.campaign_code import CampaignCode
from app.schemas.country import Country
from app.schemas.filter import Filter
from app.schemas.response_topic import ResponseTopic
from app.utils import code_hierarchy
from app.utils import filters
from app import constants

inflect_engine = inflect.engine()


class DataAccessLayer:
    def __init__(
        self,
        campaign_code: CampaignCode,
        filter_1: Filter = None,
        filter_2: Filter = None,
    ):
        self.__campaign_code = campaign_code
        self.__databank = databank.get_campaign_databank(campaign_code=campaign_code)
        self.__filter_1 = filter_1
        self.__filter_2 = filter_2

        # Apply filter 1
        if self.__filter_1:
            self.__df_1 = self.__apply_filter_to_df(
                df=self.__databank.dataframe.copy(), _filter=self.__filter_1
            )
        else:
            self.__df_1 = self.__databank.dataframe.copy()

        # Apply filter 2
        if self.__filter_2:
            self.__df_2 = self.__apply_filter_to_df(
                df=self.__databank.dataframe.copy(), _filter=self.__filter_2
            )
        else:
            self.__df_2 = self.__databank.dataframe.copy()

        # If filter_1 was requested, then do not use the cached ngrams
        self.__use_ngrams_cached = True
        if self.__filter_1:
            self.__use_ngrams_cached = False

    def __get_df_1_copy(self) -> pd.DataFrame:
        """Get dataframe 1 copy"""

        return self.__df_1.copy()

    def __get_df_2_copy(self) -> pd.DataFrame:
        """Get dataframe 2 copy"""

        return self.__df_2.copy()

    def __apply_filter_to_df(self, df: pd.DataFrame, _filter: Filter) -> pd.DataFrame:
        """Apply filter to df"""

        df = filters.apply_filter_to_df(df=df, _filter=_filter)

        return df

    def get_countries_list(self) -> list[Country]:
        """Get countries list"""

        countries = self.__databank.countries

        return list(countries.values())

    def get_countries_dict(self) -> dict[str, Country]:
        """Get countries dict"""

        countries = self.__databank.countries
        if countries:
            return countries

        return {}

    def get_country_regions(self, country_alpha2_code: str) -> list[str]:
        """Get country regions"""

        countries = self.__databank.countries
        country = countries.get(country_alpha2_code)
        if country:
            return country.regions

        return []

    def get_response_topics(self) -> list[ResponseTopic]:
        """Get response topics"""

        hierarchy = self.__databank.category_hierarchy
        response_topics = []
        for top_level, leaves in hierarchy.items():
            for code, name in leaves.items():
                response_topics.append(ResponseTopic(code=code, name=name))

        return response_topics

    def get_ages(self) -> list[str]:
        """Get ages"""

        ages = self.__databank.ages

        return ages

    def get_genders(self) -> list[str]:
        """Get genders"""

        genders = self.__databank.genders

        return genders

    def get_professions(self) -> list[str]:
        """Get professions"""

        professions = self.__databank.professions

        return professions

    def get_only_responses_from_categories_options(self) -> list[dict[str, str]]:
        """Get only responses from categories options"""

        only_responses_from_categories_options = (
            self.__databank.only_responses_from_categories_options
        )

        return only_responses_from_categories_options

    def get_only_multi_word_phrases_containing_filter_term_options(
        self,
    ) -> list[dict[str, str]]:
        """Get only multi-word phrases containing filter term options"""

        only_multi_word_phrases_containing_filter_term_options = (
            self.__databank.only_multi_word_phrases_containing_filter_term_options
        )

        return only_multi_word_phrases_containing_filter_term_options

    def get_responses_sample_columns(self) -> list[dict[str, str]]:
        """Get responses sample columns"""

        responses_sample_columns = self.__databank.responses_sample_columns

        return responses_sample_columns

    def get_respondent_noun_singular(self):
        """Get respondent noun singular"""

        respondent_noun = self.__databank.respondent_noun

        return respondent_noun

    def get_respondent_noun_plural(self):
        """Get respondent noun plural"""

        respondent_noun = self.__databank.respondent_noun

        respondent_noun_plural = inflect_engine.plural(respondent_noun)

        return respondent_noun_plural

    def get_extra_stopwords(self) -> list[str]:
        """Get extra stopwords"""

        extra_stopwords = self.__databank.extra_stopwords

        return extra_stopwords

    def get_responses_sample_data(self) -> list[dict]:
        """Get responses sample data"""

        def get_all_descriptions(code: str):
            """Get all descriptions"""

            mapping_to_description = code_hierarchy.get_mapping_to_description(
                campaign_code=self.__campaign_code
            )

            return mapping_to_description.get(
                code,
                " / ".join(
                    sorted(
                        set([mapping_to_description.get(x, x) for x in code.split("/")])
                    )
                ),
            )

        # Get copy to not modify original
        df_1_copy = self.__get_df_1_copy()

        # Get a sample of 1000
        n_sample = 1000
        if len(df_1_copy.index) > 0:
            if len(df_1_copy.index) < n_sample:
                n_sample = len(df_1_copy.index)
            df_1_copy = df_1_copy.sample(n=n_sample, random_state=1)

        df_1_copy["description"] = df_1_copy["canonical_code"].apply(
            get_all_descriptions
        )

        column_ids = [col["id"] for col in self.get_responses_sample_columns()]

        responses_sample_data = df_1_copy[column_ids].to_dict("records")

        return responses_sample_data

    def get_responses_breakdown_data(self) -> list[dict]:
        """Get responses breakdown data"""

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

    def get_n_grams(self, use_ngrams_cached: bool = False) -> tuple:
        """Get n grams"""

        # Return the cached n grams
        if use_ngrams_cached:
            ngrams_unfiltered = self.__databank.ngrams_unfiltered
            unigram_count_dict = ngrams_unfiltered.get("unigram")
            bigram_count_dict = ngrams_unfiltered.get("bigram")
            trigram_count_dict = ngrams_unfiltered.get("trigram")

            return unigram_count_dict, bigram_count_dict, trigram_count_dict

        # Get copy to not modify original
        df_1_copy = self.__get_df_1_copy()

        # Stopwords
        extra_stopwords = self.get_extra_stopwords()
        all_stopwords = constants.STOPWORDS + extra_stopwords

        # n gram counters
        unigram_count_dict = Counter()
        bigram_count_dict = Counter()
        trigram_count_dict = Counter()

        for words_list in df_1_copy["tokenized"]:
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

    def get_wordcloud_words(self) -> list[dict]:
        """Get wordcloud words"""

        unigram_count_dict, bigram_count_dict, trigram_count_dict = self.get_n_grams(
            use_ngrams_cached=self.__use_ngrams_cached
        )

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
            {"text": key, "value": item} for key, item in dict(wordcloud_words).items()
        ]

        return wordcloud_words_list
