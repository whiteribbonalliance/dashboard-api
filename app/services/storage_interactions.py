"""Fetch data from Storage"""

import logging
from datetime import datetime
from datetime import timedelta

from google.cloud import storage
from google.oauth2 import service_account

from app.logginglib import init_custom_logger

logger = logging.getLogger(__name__)
init_custom_logger(logger)

BUCKET_NAME = "wra"
EXPIRE_IN = datetime.today() + timedelta(1)  # after 1 day


def get_storage_client() -> storage.Client:
    """Get storage client"""

    credentials = service_account.Credentials.from_service_account_file(
        filename="credentials.json",
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    return storage.Client(credentials=credentials)


def create_bucket(storage_class: str = "STANDARD", location: str = "europe-west1"):
    """Create bucket"""

    storage_client = get_storage_client()
    bucket = storage_client.bucket(BUCKET_NAME)
    bucket.storage_class = storage_class
    storage_client.create_bucket(bucket, location=location)


def upload_file(source_filename: str, destination_filename: str):
    """Upload file"""

    storage_client = get_storage_client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(destination_filename)
    blob.upload_from_filename(source_filename)


def get_file_url(filename: str, expire_in: str = EXPIRE_IN) -> str:
    """Get file url"""

    storage_client = get_storage_client()
    bucket = storage_client.bucket(BUCKET_NAME)
    url = bucket.blob(filename).generate_signed_url(expire_in)

    return url


def file_exists(filename: str) -> bool:
    """Check if file exists"""

    storage_client = get_storage_client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)

    return blob.exists()


def clear_bucket():
    """Clear bucket"""

    storage_client = get_storage_client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs()
    for blob in blobs:
        blob.delete()
