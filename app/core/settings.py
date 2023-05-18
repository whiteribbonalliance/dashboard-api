import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    # General app config
    VERSION = "1.0"
    APP_TITLE = "What Women Want API"


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
