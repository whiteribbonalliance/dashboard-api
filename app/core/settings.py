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

import os
from functools import lru_cache

from pydantic import BaseSettings

from app.enums.api_prefix import ApiPrefix

# Check stage
STAGE = os.getenv("STAGE")
if not STAGE:
    raise Exception("Stage should be dev or prod.")
elif STAGE not in ["dev", "prod"]:
    raise Exception(f"Stage should be dev or prod, found {STAGE}.")

# Check cloud service
CLOUD_SERVICE = os.getenv("CLOUD_SERVICE", "").lower()
if CLOUD_SERVICE and CLOUD_SERVICE not in ["google", "azure"]:
    raise Exception(f"Invalid cloud service: {CLOUD_SERVICE}.")

# Allow origins
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "").split(" ")
ALLOW_ORIGINS = list(filter(None, ALLOW_ORIGINS))


class Settings(BaseSettings):
    STAGE: str = STAGE
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    VERSION: str = "1.0.0"
    OWNER_NAME: str = os.getenv("OWNER_NAME", "")
    OWNER_LINK: str = os.getenv("OWNER_LINK", "")
    COMPANY_NAME: str = os.getenv("COMPANY_NAME", "")
    COMPANY_LINK: str = os.getenv("COMPANY_LINK", "")
    ACCESS_TOKEN_SECRET_KEY: str = os.getenv("ACCESS_TOKEN_SECRET_KEY")
    GOOGLE_CREDENTIALS_JSON: str = os.getenv("GOOGLE_CREDENTIALS_JSON")
    API_PREFIX: str = ApiPrefix.v1.value
    TRANSLATIONS_ENABLED: bool = os.getenv("TRANSLATIONS_ENABLED", "").lower() == "true"
    NEWRELIC_API_KEY: str = os.getenv("NEWRELIC_API_KEY")
    NEW_RELIC_URL: str = os.getenv("NEW_RELIC_URL")
    CLOUD_SERVICE: str = CLOUD_SERVICE
    RELOAD_DATA_EVERY_12TH_HOUR: bool = (
        os.getenv("RELOAD_DATA_EVERY_12TH_HOUR", "").lower() == "true"
    )
    INCLUDE_ALLCAMPAIGNS: bool = os.getenv("INCLUDE_ALLCAMPAIGNS", "") == "true"

    # Google
    GOOGLE_CLOUD_STORAGE_BUCKET_FILE: str = os.getenv(
        "GOOGLE_CLOUD_STORAGE_BUCKET_FILE"
    )
    GOOGLE_CLOUD_STORAGE_BUCKET_TMP_DATA: str = os.getenv(
        "GOOGLE_CLOUD_STORAGE_BUCKET_TMP_DATA", ""
    )

    # Azure
    AZURE_TRANSLATOR_KEY: str = os.getenv("AZURE_TRANSLATOR_KEY")
    AZURE_STORAGE_CONNECTION_STRING: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    AZURE_STORAGE_ACCOUNT_KEY: str = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    AZURE_STORAGE_ACCOUNT_NAME: str = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    AZURE_STORAGE_CONTAINER_FILE: str = os.getenv("AZURE_STORAGE_CONTAINER_FILE")
    AZURE_STORAGE_CONTAINER_TMP_DATA: str = os.getenv(
        "AZURE_STORAGE_CONTAINER_TMP_DATA"
    )

    # Only for legacy campaigns
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY")


class DevSettings(Settings):
    DEBUG: bool = True
    RELOAD: bool = True
    CORS: dict = {
        "allow_origins": ["*"],
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }


class ProdSettings(Settings):
    DEBUG: bool = False
    RELOAD: bool = False
    CORS: dict = {
        "allow_origins": ALLOW_ORIGINS,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "OPTIONS", "HEAD"],
        "allow_headers": [
            "Access-Control-Allow-Headers",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Credentials",
            "Access-Control-Allow-Origin",
            "Access-Control-Max-Age",
            "Authorization",
            "Content-Type",
            "Set-Cookie",
        ],
    }


@lru_cache()
def get_settings():
    if STAGE == "dev":
        return DevSettings()
    if STAGE == "prod":
        return ProdSettings()
