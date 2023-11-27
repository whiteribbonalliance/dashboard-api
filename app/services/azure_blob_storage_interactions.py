"""Azure Blob Storage interactions"""

from datetime import datetime, timedelta
from io import StringIO

import pandas as pd
from azure.storage.blob import (
    ContainerClient,
    BlobSasPermissions,
    BlobClient,
    generate_blob_sas,
)
from app.types import AzureBlobStorageContainerName
from app import env

EXPIRE_IN = datetime.today() + timedelta(3)  # after 3 days


def get_container_client(
    container_name: AzureBlobStorageContainerName,
) -> ContainerClient:
    """Get container client"""

    if container_name == "csv":
        return ContainerClient.from_connection_string(
            conn_str=env.AZURE_STORAGE_CONNECTION_STRING,
            container_name=container_name,
        )
    elif container_name == "main":
        return ContainerClient.from_connection_string(
            conn_str=env.AZURE_STORAGE_CONNECTION_STRING,
            container_name=container_name,
        )


def cleanup(container_name: AzureBlobStorageContainerName, limit_gb: int = 5):
    """Cleanup"""

    # Get container client
    container_client = get_container_client(container_name=container_name)

    # Get size of all files
    size_bytes = 0
    blob_list = container_client.list_blobs()
    for blob in blob_list:
        size_bytes += blob.size

    # Get size in megabytes
    size_megabytes = size_bytes / 1024 / 1024

    # Clear bucket
    if size_megabytes >= (limit_gb * 1024):
        clear_container(container_name=container_name)


def clear_container(container_name: AzureBlobStorageContainerName):
    """Clear container"""

    # Get container client
    container_client = get_container_client(container_name=container_name)

    # Get list
    blob_list = container_client.list_blobs()

    # Delete blobs
    for blob in blob_list:
        container_client.delete_blob(blob.name)


def upload_df_as_csv(
    container_name: AzureBlobStorageContainerName, df: pd.DataFrame, csv_filename: str
):
    """Upload dataframe as CSV"""

    # Get container client
    container_client = get_container_client(container_name=container_name)

    # Save to buffer
    buffer = StringIO()
    df.to_csv(path_or_buf=buffer, index=False, header=True)

    # Upload
    container_client.upload_blob(name=csv_filename, data=buffer.getvalue())


def blob_exists(container_name: AzureBlobStorageContainerName, blob_name: str) -> bool:
    """Check if blob exists"""

    # Get blob
    blob = BlobClient.from_connection_string(
        conn_str=env.AZURE_STORAGE_CONNECTION_STRING,
        container_name=container_name,
        blob_name=blob_name,
    )

    return blob.exists()


def get_blob_url(container_name: AzureBlobStorageContainerName, blob_name: str) -> str:
    """Get blob url"""

    sas_blob = generate_blob_sas(
        account_name=env.AZURE_STORAGE_ACCOUNT_NAME,
        container_name=container_name,
        blob_name=blob_name,
        account_key=env.AZURE_STORAGE_ACCOUNT_KEY,
        permission=BlobSasPermissions(read=True),
        expiry=EXPIRE_IN,
    )

    return f"https://{env.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{container_name}/{blob_name}?{sas_blob}"
