import asyncio

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.settings import settings
from app.scheduler import app as app_rocketry
from app.utils import data_loader

# Load initial data before starting the application
data_loader.load_data()
data_loader.load_translations_cache()

description = """
What Women Want Dashboard API.
"""

app_fastapi = FastAPI(
    title=settings.APP_TITLE,
    description=description,
    version=settings.VERSION,
    docs_url="/docs",
    contact={
        "name": "Thomas Wood",
        "url": "https://fastdatascience.com",
    },
)

app_fastapi.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS["origins"],
    allow_credentials=settings.CORS["allow_credentials"],
    allow_methods=settings.CORS["allow_methods"],
    allow_headers=settings.CORS["allow_headers"],
)

app_fastapi.include_router(api_router, prefix=settings.API_V1)


class Server(uvicorn.Server):
    """
    Custom uvicorn.Server
    Override signals and include Rocketry
    """

    def handle_exit(self, sig: int, frame):
        app_rocketry.session.shut_down()

        return super().handle_exit(sig, frame)


async def main():
    # Create API task
    server = Server(
        config=uvicorn.Config(
            app=app_fastapi,
            host=settings.SERVER_HOST,
            port=settings.PORT,
            reload=settings.RELOAD,
            workers=1,
            loop="asyncio",
        )
    )
    api = asyncio.create_task(server.serve())

    # Create scheduler task
    scheduler = asyncio.create_task(app_rocketry.serve())

    # Start both applications (FastAPI & Rocketry)
    print("INFO:\t  Starting applications...")
    await asyncio.wait([scheduler, api])


if __name__ == "__main__":
    asyncio.run(main())
