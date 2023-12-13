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

from pydantic import ValidationError

from app.schemas.campaign_config import CampaignConfig

CAMPAIGNS_CONFIG: dict[str, CampaignConfig] = {}

campaigns_config_folder = "campaigns-config"

for config_folder in os.listdir(os.path.join(campaigns_config_folder)):
    # Check if it is a folder
    if not os.path.isdir(os.path.join(campaigns_config_folder, config_folder)):
        continue

    if config_folder == "example":
        continue

    # Load config
    config_json = os.path.join(campaigns_config_folder, config_folder, "config.json")
    if os.path.isfile(config_json):
        with open(config_json, "r") as file:
            try:
                config = CampaignConfig.parse_obj(json.loads(file.read()))
            except ValidationError:
                raise Exception(
                    f"Could not validate configuration found in config folder {config_folder}."
                )

    # Check if CSV file exists
    csv_file = os.path.join(campaigns_config_folder, config_folder, config.filename)
    if not os.path.isfile(csv_file):
        raise Exception(
            f"File {config.filename} was not found in config folder {config_folder}."
        )
    config.filepath = os.path.join(csv_file)

    # Check for duplicate campaign code
    if config.code not in CAMPAIGNS_CONFIG:
        CAMPAIGNS_CONFIG[config.code] = config
    else:
        raise Exception(f"Duplicate campaign code found {config.code}.")
