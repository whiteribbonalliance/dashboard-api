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
    # Development app config
    SERVER_HOST = "0.0.0.0"
    DEBUG = True
    PORT = 8000
    RELOAD = True
    CORS = {
        "origins": [
            "*",
        ],
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }


class ProdSettings(Settings):
    # Production app config
    SERVER_HOST = "0.0.0.0"
    DEBUG = False
    PORT = 8080
    RELOAD = False
    CORS = {
        "origins": [
            "*",
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
