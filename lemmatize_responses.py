import os

import nltk
import pandas as pd
from pywsd.utils import lemmatize_sentence

from app.utils.campaigns_config_loader import CAMPAIGNS_CONFIG

nltk.download("averaged_perceptron_tagger")
nltk.download("wordnet")
nltk.download("punkt")


def lemmatize_all_data():
    """
    Lemmatize all data.
    """

    for campaign_config in CAMPAIGNS_CONFIG:
        campaign_path = campaign_config["path"]

        print(f"Lemmatizing responses in {campaign_path}...")

        # File path
        filepath = os.path.join("data", campaign_path)

        # Load dataframe
        df = pd.read_csv(filepath_or_buffer=filepath, keep_default_na=False)

        # Get all raw response columns
        raw_response_columns = []
        for column in df.columns.tolist():
            if column.startswith("q") and column.endswith("_raw_response"):
                q_code_number = column.replace("_raw_response", "", 1).replace(
                    "q", "", 1
                )
                if q_code_number.isnumeric():
                    raw_response_columns.append(column)
                else:
                    raise Exception(f"Invalid column name: {column}")

        # Lemmatize
        for column in raw_response_columns:
            q_code_number = column.replace("_raw_response", "", 1).replace("q", "", 1)
            q_code = f"q{q_code_number}"
            lemmatized_column_name = f"{q_code}_lemmatized"
            df[lemmatized_column_name] = df[column].apply(lemmatize_text)
            df.to_csv(path_or_buf=filepath, index=False, header=True)


def lemmatize_text(text: str) -> str:
    """
    Lemmatize text.
    """

    if pd.isna(text):
        return ""
    else:
        return " ".join(lemmatize_sentence(sentence=text))


lemmatize_all_data()
