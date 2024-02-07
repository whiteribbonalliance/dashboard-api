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

import pandas as pd


def find_in_df(df: pd.DataFrame) -> list[str]:
    """
    Find q codes by analysing df.
    q1 refers to the question from which the respondent gave a response.
    If q1 is included that means that the columns q1_response and q1_canonical_code are present.
    There can be multiple questions e.g. q1, q2, q3 etc.
    """

    campaign_q_codes: list[str] = []

    columns_list = df.columns.tolist()
    for column in columns_list:
        # Check if q[NUMBER]_response column is present
        if column.startswith("q") and column.endswith("_response"):
            # Extract q code number
            q_code_number = column.replace("_response", "", 1).replace("q", "", 1)

            # Check if q code number value is numeric
            if q_code_number.isnumeric():
                # Check if required column q[NUMBER]_canonical_code is present
                if f"q{q_code_number}_canonical_code" in columns_list:
                    campaign_q_codes.append(f"q{q_code_number}")
                else:
                    raise Exception(
                        f"Required column q{q_code_number}_canonical_code not found."
                    )

    if not campaign_q_codes:
        raise Exception("Required q1_response column not found.")

    return campaign_q_codes
