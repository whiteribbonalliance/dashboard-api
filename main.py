import asyncio

import uvicorn
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app import env
from app import helpers
from app.api.v1.api import api_router
from app.core.settings import settings
from app.scheduler import app as app_rocketry

description = """
What Women Want Dashboard API.
"""

# Create dirs required in local development.
# In production these dirs are already present.
if env.STAGE == "dev" and not env.ONLY_PMNCH:
    helpers.create_tmp_dir_if_not_exists()
if env.STAGE == "dev" and env.ONLY_PMNCH:
    helpers.create_pmnch_main_dir_if_not_exists()
    helpers.create_pmnch_csv_dir_if_not_exists()

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
    middleware_class=CORSMiddleware,
    allow_origins=settings.CORS["allow_origins"],
    allow_credentials=settings.CORS["allow_credentials"],
    allow_methods=settings.CORS["allow_methods"],
    allow_headers=settings.CORS["allow_headers"],
)

app_fastapi.include_router(api_router, prefix=settings.API_V1)


@app_fastapi.get(path="/", status_code=status.HTTP_200_OK)
def index():
    return {"message": "API to supply dashboard with response data."}


class Server(uvicorn.Server):
    """
    Custom uvicorn.Server
    Override signals and include Rocketry
    """

    def handle_exit(self, sig: int, frame):
        app_rocketry.session.shut_down()

        return super().handle_exit(sig, frame)


async def main():
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
    scheduler = asyncio.create_task(app_rocketry.serve())

    # Start both applications (FastAPI & Rocketry)
    print("INFO:\t  Starting applications...")
    await asyncio.wait([scheduler, api])


if __name__ == "__main__":
    asyncio.run(main())
