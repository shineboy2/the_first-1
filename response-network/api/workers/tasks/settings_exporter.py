"""
Export settings to Request Network (Synchronous version)
"""
from datetime import datetime
import json
import os
import io
from pathlib import Path
import ftplib
import logging

from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from models.settings import Settings

# Load .env file
load_dotenv()

logger = logging.getLogger(__name__)

@shared_task
def export_settings_to_request_network():
    """
    Export settings to Request Network (Sync).
    
    DISABLED: Settings export is no longer needed as request-network manages its own settings.
    User data and access controls are exported via users_exporter.py instead.
    """
    logger.info("Settings export is disabled - request-network manages its own configuration.")
    return {
        "status": "disabled",
        "reason": "Settings export has been deprecated. User data including permissions is exported via users_exporter.py"
    }