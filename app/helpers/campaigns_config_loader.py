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

import validators
from pydantic import ValidationError

from app.core.settings import get_settings
from app.schemas.campaign_config import CampaignConfigInternal

settings = get_settings()

CAMPAIGNS_CONFIG: dict[str, CampaignConfigInternal] = {}

campaigns_configurations_folder = "campaigns-configurations"

print("INFO:\t  Loading configurations...")

for config_folder in os.listdir(os.path.join(campaigns_configurations_folder)):
    # Check if it is a folder
    if not os.path.isdir(os.path.join(campaigns_configurations_folder, config_folder)):
        continue

    # Skip example
    if config_folder == "example":
        continue

    # Load config
    config_json = os.path.join(
        campaigns_configurations_folder, config_folder, "config.json"
    )
    if os.path.isfile(config_json):
        with open(config_json, "r", encoding="utf8") as file:
            try:
                config = CampaignConfigInternal.parse_obj(json.loads(file.read()))
            except ValidationError as e:
                raise Exception(
                    f"Could not validate configuration found in config folder {config_folder}. Error: {str(e)}"
                )

    # allcampaigns path is reserved
    if settings.INCLUDE_ALLCAMPAIGNS and config.dashboard_path == "allcampaigns":
        raise Exception("The path allcampaigns is reserved.")

    # Only one file location should be provided
    if (
        sum([bool(config.file.local), bool(config.file.url), bool(config.file.cloud)])
        != 1
    ):
        raise Exception("Provide one file location.")

    # Check url
    if config.file.url:
        if not validators.url(config.file.url):
            raise Exception(f"{config.file.url} is not a valid link.")

    # Check CSV file
    if config.file.local:
        csv_file = os.path.join(
            campaigns_configurations_folder, config_folder, config.file.local
        )
        if not config.file.local.endswith(".csv"):
            raise Exception("Invalid CSV file name.")
        if not os.path.isfile(csv_file):
            raise Exception(
                f"File {config.file} was not found in config folder {config_folder}."
            )
        config.filepath = csv_file

    # Check for duplicate dashboard path
    if config.dashboard_path in [x.dashboard_path for x in CAMPAIGNS_CONFIG.values()]:
        raise Exception(f"Duplicate dashboard path found at {config.campaign_code}.")

    # Check for duplicate campaign code
    if config.campaign_code not in CAMPAIGNS_CONFIG:
        CAMPAIGNS_CONFIG[config.campaign_code] = config
    else:
        raise Exception(f"Duplicate campaign code found at {config.campaign_code}.")
