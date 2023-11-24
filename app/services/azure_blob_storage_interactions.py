"""Azure Blob Storage interactions"""

import os
import glob

import pandas as pd

from app.types import AzureBlobStorageContainerMountPath


def cleanup(mount_path: AzureBlobStorageContainerMountPath, limit_gb: int = 5):
    """Cleanup"""

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
        clear_container(mount_path=mount_path)


def clear_container(mount_path: AzureBlobStorageContainerMountPath):
    """Clear container"""

    try:
        files = glob.glob(os.path.join(mount_path, "*"))
        for file in files:
            if os.path.isfile(file):
                os.remove(file)
    except OSError:
        pass


def upload_df_as_csv_file(
    df: pd.DataFrame, mount_path: AzureBlobStorageContainerMountPath, csv_filename: str
):
    """Upload dataframe as CSV file"""

    df.to_csv(path_or_buf=f"{mount_path}/{csv_filename}", index=False, header=True)
