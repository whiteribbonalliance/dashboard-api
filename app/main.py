import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.settings import settings
from app.utils import data_loader

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

app.include_router(api_router, prefix=settings.API_V1)


@app.on_event("startup")
def startup_event():
    data_loader.load_initial_data()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
