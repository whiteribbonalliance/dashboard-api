import pandas as pd


def find_in_df(df: pd.DataFrame) -> list[str]:
    """
    Find q codes by analysing df.
    """

    campaign_q_codes: list[str] = []

    for column in df.columns.tolist():
        if column.startswith("q") and column.endswith("_raw_response"):
            q_code_number = column.replace("_raw_response", "", 1).replace("q", "", 1)
            if q_code_number.isnumeric():
                campaign_q_codes.append(f"q{q_code_number}")

    return campaign_q_codes
