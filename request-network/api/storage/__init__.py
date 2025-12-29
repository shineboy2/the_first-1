"""Storage handlers package."""

from .base import StorageHandler
from .local import LocalStorageHandler
from .ftp import FTPStorageHandler
# S3 excluded to minimize dependencies for now
# from .s3 import S3StorageHandler

# Map storage types to handler classes
STORAGE_HANDLERS = {
    "local": LocalStorageHandler,
    "ftp": FTPStorageHandler,
    # "s3": S3StorageHandler,
}
