"""
MIT License

Copyright (c) 2023 White Ribbon Alliance. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

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

import sys

import nltk
import pandas as pd
from pywsd.utils import lemmatize_sentence

from app.enums.legacy_campaign_code import LegacyCampaignCode
from app.helpers import q_col_names, q_codes_finder
from app.helpers.campaigns_config_loader import CAMPAIGNS_CONFIG

nltk.download("averaged_perceptron_tagger")
nltk.download("wordnet")
nltk.download("punkt")

# Will only lemmatize these campaigns if provided
campaign_codes_from_args = []
if len(sys.argv) > 1:
    campaign_codes_from_args = sys.argv[1:]


def lemmatize():
    """
    Lemmatize.
    """

    if not campaign_codes_from_args:
        print("Nothing to lemmatize.")
        return

    for campaign_config in CAMPAIGNS_CONFIG.values():
        if campaign_config.campaign_code in [x.value for x in LegacyCampaignCode]:
            continue

        if campaign_codes_from_args:
            if campaign_config.campaign_code not in campaign_codes_from_args:
                continue

        if not campaign_config.file.local:
            raise Exception("No file was provided.")

        print(f"Lemmatizing responses in {campaign_config.file.local}...")

        # Load dataframe
        df = pd.read_csv(
            filepath_or_buffer=campaign_config.filepath, keep_default_na=False
        )

        # Get q codes
        q_codes = q_codes_finder.find_in_df(df=df)

        for q_code in q_codes:
            response_column = f"{q_code}_response"

            # Lemmatize
            lemmatized_column_name = q_col_names.get_lemmatized_col_name(q_code=q_code)
            df[lemmatized_column_name] = df[response_column].apply(lemmatize_text)

            df.to_csv(path_or_buf=campaign_config.filepath, index=False, header=True)


def lemmatize_text(text: str) -> str:
    """
    Lemmatize text.
    """

    if not text or pd.isna(text):
        return ""
    else:
        return " ".join(lemmatize_sentence(sentence=text))


lemmatize()
