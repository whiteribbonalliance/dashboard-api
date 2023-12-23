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

import asyncio

import uvicorn
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app import databases
from app import utils
from app.api.v1.api import api_router
from app.core.settings import get_settings
from app.helpers.campaigns_config_loader import CAMPAIGNS_CONFIG
from app.scheduler import app as app_rocketry

settings = get_settings()

# Create dirs required in local development.
# In production these dirs are already present.
if settings.STAGE == "dev":
    utils.create_tmp_dir_if_not_exists()

# Create in-memory Database objects
databases.create_databases(
    campaign_codes=[x.campaign_code for x in CAMPAIGNS_CONFIG.values()]
)

# Tags metadata
tags_metadata = [
    {
        "name": "Campaigns",
        "description": "Read or download data related to campaigns.",
    },
    {
        "name": "Campaigns Configurations",
        "description": "Read campaigns configurations.",
    },
    {
        "name": "Campaigns Merged",
        "description": "Read data of all campaigns merged together as one campaign.",
    },
    {
        "name": "Authentication",
        "description": "Login and receive a token. This token can be used to access protected routes that allow downloading campaigns data.",
    },
    {
        "name": "Data",
        "description": "Allows reloading the data from source and check loading status. Only useful if CSV file is hosted externally.",
    },
    {
        "name": "GeoJSON World",
        "description": "Read GeoJSON world data.",
    },
    {
        "name": "TopoJSON",
        "description": "Read TopoJSON. Only supports alpha2-code MX.",
    },
    {
        "name": "App Settings",
        "description": "Read app settings.",
    },
]

app_fastapi = FastAPI(
    title="Dashboard API",
    description="This API is used for providing campaign data to display in a dashboard.",
    version=settings.VERSION,
    docs_url="/docs",
    openapi_tags=tags_metadata,
    contact={
        "name": settings.OWNER_NAME,
        "url": settings.OWNER_LINK,
    },
)

app_fastapi.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=settings.CORS["allow_origins"],
    allow_credentials=settings.CORS["allow_credentials"],
    allow_methods=settings.CORS["allow_methods"],
    allow_headers=settings.CORS["allow_headers"],
)

app_fastapi.include_router(api_router, prefix=settings.API_PREFIX)


@app_fastapi.get(path="/", status_code=status.HTTP_200_OK, tags=["Index"])
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
            host=settings.HOST,
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
