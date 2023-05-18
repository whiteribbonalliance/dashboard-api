import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.routers.health_check_router import router as health_check_router
from app.routers.info_router import router as info_router
from app.routers.text_router import router as text_router
from app.enums.campaigns import Campaigns

# TODO: TEST
from app.utils.data_loader import get_campaign_df
df = get_campaign_df(campaign=Campaigns.what_young_people_want.value)
print(df)

description = """
What Women Want Dashboard API.
"""

app = FastAPI(
    title=settings.APP_TITLE,
    description=description,
    version=settings.VERSION,
    docs_url="/docs",
    contact={
        "name": "Thomas Wood",
        "url": "https://fastdatascience.com",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS["origins"],
    allow_credentials=settings.CORS["allow_credentials"],
    allow_methods=settings.CORS["allow_methods"],
    allow_headers=settings.CORS["allow_headers"],
)

app.include_router(health_check_router, tags=["Health Check"])
app.include_router(text_router, tags=["Text"])
app.include_router(info_router, tags=["Info"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
