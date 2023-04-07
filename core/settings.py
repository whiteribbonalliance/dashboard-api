import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    # General app config
    VERSION = "1.0"
    APP_TITLE = "What Women Want API"


class DevSettings(Settings):
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
    # TODO change
    SERVER_HOST = "0.0.0.0"
    DEBUG = False
    PORT = 80
    RELOAD = False
    CORS = {
        "origins": [
            "*",
        ],
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }


def get_settings():
    env = os.getenv("STAGE", "dev")
    settings_type = {
        "dev": DevSettings(),
        "prod": ProdSettings(),
    }
    return settings_type[env]


settings: Settings = get_settings()
