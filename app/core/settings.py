import os

from pydantic import BaseSettings

from app.enums.api_prefix import ApiPrefix


class Settings(BaseSettings):
    VERSION: str = "1.0.0"
    APP_TITLE: str = "What Women Want API"
    API_V1: str = ApiPrefix.v1.value


class DevSettings(Settings):
    COOKIE_DOMAIN: str = "localhost"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "strict"
    SERVER_HOST: str = "0.0.0.0"
    DEBUG: bool = True
    PORT: int = 8000
    RELOAD: bool = True
    CORS: dict = {
        "allow_origins": [
            "http://localhost",
            "http://localhost:3000",
            "http://explore.whiteribbonalliance.local:3000",
        ],
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }


class ProdSettings(Settings):
    COOKIE_DOMAIN: str = ".whiteribbonalliance.org"
    COOKIE_SECURE: bool = True
    COOKIE_SAMESITE: str = "strict"
    SERVER_HOST: str = "0.0.0.0"
    DEBUG: bool = False
    PORT: int = 8080
    RELOAD: bool = False
    CORS: dict = {
        "allow_origins": [
            "http://localhost",
            "http://localhost:3000",
            "http://explore.whiteribbonalliance.local:3000",
            "https://explore.whiteribbonalliance.org",
            "https://whatwomenwant.whiteribbonalliance.org",
            "https://whatyoungpeoplewant.whiteribbonalliance.org",
            "https://midwivesvoices.whiteribbonalliance.org",
            "https://admin.whiteribbonalliance.org",
        ],
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }


env = os.getenv("STAGE")
if env == "dev":
    settings = DevSettings()
else:
    settings = ProdSettings()
