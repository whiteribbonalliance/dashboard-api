"""Azure Blob Storage interactions"""

import os
import glob
from io import StringIO

import pandas as pd
from azure.storage.blob import ContainerClient

from app.types import AzureBlobStorageContainerMountPath, AzureContainerName
from app import env


def get_container_client(container_name: AzureContainerName) -> ContainerClient:
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


def cleanup(container_name: AzureContainerName, limit_gb: int = 5):
    """Cleanup"""

    # Get mount path
    mount_path = get_container_mount_path(container_name=container_name)

    # Get size of all files
    size_bytes = 0
    for path, dirs, files in os.walk(mount_path):
        for f in files:
            fp = os.path.join(path, f)
            size_bytes += os.path.getsize(fp)

    # Get size in megabytes
    size_megabytes = size_bytes / 1024 / 1024

    # Clear bucket
    if size_megabytes >= (limit_gb * 1024):
        clear_container(container_name=container_name)


def clear_container(container_name: AzureContainerName):
    """Clear container"""

    if env.STAGE == "prod":
        # Get container client
        container_client = get_container_client(container_name=container_name)

        # Get list
        blob_list = container_client.list_blobs()

        # Delete blobs
        for blob in blob_list:
            container_client.delete_blob(blob.name)
    else:
        # Get mount path
        mount_path = get_container_mount_path(container_name=container_name)

        files = glob.glob(os.path.join(mount_path, "*"))
        for file in files:
            if os.path.isfile(file):
                try:
                    os.remove(file)
                except OSError:
                    pass


def upload_df_as_csv(
    container_name: AzureContainerName, df: pd.DataFrame, csv_filename: str
):
    """Upload dataframe as CSV"""

    if env.STAGE == "prod":
        # Get container client
        container_client = get_container_client(container_name=container_name)

        # Save to buffer
        buffer = StringIO()
        df.to_csv(path_or_buf=buffer, index=False, header=True)

        # Upload
        container_client.upload_blob(name=csv_filename, data=buffer.getvalue())
    else:
        # Get mount path
        mount_path = get_container_mount_path(container_name=container_name)

        df.to_csv(path_or_buf=f"{mount_path}/{csv_filename}", index=False, header=True)


def get_container_mount_path(container_name: AzureContainerName):
    """Get container mount path"""

    if container_name == "main":
        mount_path: AzureBlobStorageContainerMountPath = "/pmnch_main"
        return mount_path
    elif container_name == "csv":
        mount_path: AzureBlobStorageContainerMountPath = "/pmnch_csv"
        return mount_path
