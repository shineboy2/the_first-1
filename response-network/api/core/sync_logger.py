import logging
import os
from pathlib import Path

# Ensure logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Setup sync logger
sync_logger = logging.getLogger("sync_logger")
sync_logger.setLevel(logging.INFO)

# Create file handler
file_handler = logging.FileHandler(LOGS_DIR / "sync.log")
file_handler.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(module)s] - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
if not sync_logger.handlers:
    sync_logger.addHandler(file_handler)
    sync_logger.addHandler(console_handler)
