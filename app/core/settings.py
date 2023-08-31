import os

from pydantic import BaseSettings

from app.enums.api_prefix import ApiPrefix


class Settings(BaseSettings):
    # General app config
    VERSION = "1.0.0"
    APP_TITLE = "What Women Want API"
    API_V1 = ApiPrefix.v1
    OFFLINE_TRANSLATE_MODE = False


class DevSettings(Settings):
    COOKIE_DOMAIN: str | None = None
    COOKIE_SECURE = False
    COOKIE_SAMESITE = "none"
    SERVER_HOST = "0.0.0.0"
    DEBUG = True
    PORT = 8000
    RELOAD = True
    CORS = {
        "allow_origins": [
            "http://localhost:3000",
        ],
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }


class ProdSettings(Settings):
    COOKIE_DOMAIN: str | None = "localhost"
    COOKIE_SECURE = True
    COOKIE_SAMESITE = "strict"
    SERVER_HOST = "0.0.0.0"
    DEBUG = False
    PORT = 8080
    RELOAD = False
    CORS = {
        "allow_origins": [
            "localhost",
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
