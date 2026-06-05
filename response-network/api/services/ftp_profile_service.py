"""
Service layer for FTP Profile operations.
Provides FTPStorageHandler instances from profile configurations
and connection testing capabilities.
"""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from models.ftp_profile import FTPProfile
from schemas.ftp_profile import FTPProfileTestResult
from storage.ftp import FTPStorageHandler

logger = logging.getLogger(__name__)


class FTPProfileService:
    """Service for working with FTP profiles."""

    @staticmethod
    def get_handler_from_profile(profile: FTPProfile) -> FTPStorageHandler:
        """
        Create an FTPStorageHandler from a profile model instance.
        Can be used in both sync and async contexts.
        """
        settings = {
            "host": profile.host,
            "port": profile.port or 21,
            "username": profile.username or "anonymous",
            "password": profile.password or "",
            "base_path": profile.base_path or "/",
            "use_tls": profile.use_tls,
        }
        return FTPStorageHandler(settings)

    @staticmethod
    async def get_handler(db: AsyncSession, profile_id: UUID) -> Optional[FTPStorageHandler]:
        """
        Get an FTPStorageHandler for a given profile ID (async).
        Returns None if profile not found or inactive.
        """
        profile = await db.get(FTPProfile, profile_id)
        if not profile or not profile.is_active:
            return None
        return FTPProfileService.get_handler_from_profile(profile)

    @staticmethod
    def get_handler_sync(db: Session, profile_id: UUID) -> Optional[FTPStorageHandler]:
        """
        Get an FTPStorageHandler for a given profile ID (sync — for Celery tasks).
        Returns None if profile not found or inactive.
        """
        profile = db.get(FTPProfile, profile_id)
        if not profile or not profile.is_active:
            return None
        return FTPProfileService.get_handler_from_profile(profile)

    @staticmethod
    async def test_connection(db: AsyncSession, profile_id: UUID) -> FTPProfileTestResult:
        """
        Test FTP connection for a profile and update last_tested_at / last_test_result.
        """
        profile = await db.get(FTPProfile, profile_id)
        if not profile:
            return FTPProfileTestResult(
                success=False,
                message="FTP profile not found",
                can_read=False,
                can_write=False,
                tested_at=datetime.utcnow()
            )

        handler = FTPProfileService.get_handler_from_profile(profile)
        tested_at = datetime.utcnow()

        try:
            # Test basic connection
            connection_ok = await handler.test_connection()
            if not connection_ok:
                result = FTPProfileTestResult(
                    success=False,
                    message="Connection failed: Could not connect or authenticate",
                    can_read=False,
                    can_write=False,
                    tested_at=tested_at
                )
            else:
                # Test read access (list files)
                can_read = True
                try:
                    await handler.list_files("")
                except Exception:
                    can_read = False

                # Test write access (try upload/delete a test file)
                can_write = False
                try:
                    import tempfile
                    import os
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".test", mode="w"
                    ) as tmp:
                        tmp.write("ftp_profile_test")
                        tmp_path = tmp.name

                    test_remote = ".ftp_profile_test_write"
                    upload_ok = await handler.upload_file(tmp_path, test_remote)
                    if upload_ok:
                        can_write = True
                        await handler.delete_file(test_remote)
                    os.unlink(tmp_path)
                except Exception:
                    pass

                result = FTPProfileTestResult(
                    success=True,
                    message="Connection successful",
                    can_read=can_read,
                    can_write=can_write,
                    tested_at=tested_at
                )

        except Exception as e:
            logger.error(f"FTP connection test failed for profile {profile.name}: {e}")
            result = FTPProfileTestResult(
                success=False,
                message=f"Connection error: {str(e)[:200]}",
                can_read=False,
                can_write=False,
                tested_at=tested_at
            )

        # Update profile with test results
        profile.last_tested_at = tested_at
        profile.last_test_result = result.message
        await db.commit()

        return result
