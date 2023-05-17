import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.settings import settings
from routers.health_check_router import router as health_check_router
from routers.info_router import router as info_router
from routers.text_router import router as text_router

description = """
What Women Want Dashboard API.
"""


def configure_app():
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

    # Include routers
    app.include_router(health_check_router, tags=["Health Check"])
    app.include_router(text_router, tags=["Text"])
    app.include_router(info_router, tags=["Info"])

    return app, settings


app, settings = configure_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
