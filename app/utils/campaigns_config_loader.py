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

import json
import os

config_file = "campaigns-config.json"

with open(config_file, "r") as file:
    CAMPAIGNS_CONFIG = json.loads(file.read())

    # List to heck for campaign codes that appear more than once
    found_campaign_codes: list[str] = []

    for campaign_config in CAMPAIGNS_CONFIG:
        # Check if values are not empty
        campaign_code = campaign_config.get("code")
        campaign_file = campaign_config.get("file")
        if not campaign_code:
            raise Exception(f"A campaign code was not specified in {config_file}.")
        if not campaign_file:
            raise Exception(f"A campaign file was not specified in {config_file}.")

        # Check if file exists
        if not os.path.isfile(os.path.join("data", campaign_file)):
            raise Exception(f"File {campaign_file} was not found in data folder.")

        # Check for duplicates
        if campaign_code not in found_campaign_codes:
            found_campaign_codes.append(campaign_code)
        else:
            raise Exception(
                f"Campaign code {campaign_code} was specified twice in {config_file}."
            )
