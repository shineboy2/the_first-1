"""
Object Storage Handler — Downloads objects from S3-compatible storage
(Ceph, MinIO, AWS S3) and converts them to base64.

Uses boto3 with S3-compatible API which works with all three providers.
"""
import base64
import logging
import mimetypes
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from time import time
from typing import Any, Dict, List, Optional

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError, EndpointConnectionError

from models.object_storage_config import ObjectStorageConfig

logger = logging.getLogger(__name__)


class ObjectStorageHandler:
    """
    Handler for downloading objects from S3-compatible storage.
    Supports Ceph, MinIO, and AWS S3.
    """

    def __init__(self, config: ObjectStorageConfig):
        """
        Initialize handler with an ObjectStorageConfig model instance.
        Creates a boto3 S3 client configured for the target storage.
        """
        self.config = config
        self.default_bucket = config.default_bucket

        # Build boto3 client
        boto_config = BotoConfig(
            s3={"addressing_style": "path" if config.path_style else "virtual"},
            connect_timeout=config.timeout,
            read_timeout=config.timeout,
            retries={"max_attempts": 2, "mode": "standard"},
        )

        self.client = boto3.client(
            "s3",
            endpoint_url=config.endpoint_url,
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.get_secret_key(),
            region_name=config.region,
            use_ssl=config.use_ssl,
            verify=config.verify_ssl if config.use_ssl else False,
            config=boto_config,
        )

    def download_as_base64(
        self,
        object_key: str,
        bucket: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Download a single object and return as base64 data URI.

        Args:
            object_key: The key/path of the object in the bucket.
            bucket: Override bucket name (uses default_bucket if None).

        Returns:
            {
                "success": True/False,
                "data": "data:image/jpeg;base64,/9j/...",
                "content_type": "image/jpeg",
                "size_bytes": 45231,
                "object_key": "faces/photo.jpg",
                "error": None or "error message"
            }
        """
        target_bucket = bucket or self.default_bucket

        try:
            response = self.client.get_object(
                Bucket=target_bucket,
                Key=object_key,
            )
            body = response["Body"].read()
            content_type = response.get("ContentType", "application/octet-stream")

            # If content_type is generic, try to guess from extension
            if content_type == "application/octet-stream" or content_type == "binary/octet-stream":
                guessed_type, _ = mimetypes.guess_type(object_key)
                if guessed_type:
                    content_type = guessed_type

            b64_encoded = base64.b64encode(body).decode("utf-8")
            data_uri = f"data:{content_type};base64,{b64_encoded}"

            return {
                "success": True,
                "data": data_uri,
                "content_type": content_type,
                "size_bytes": len(body),
                "object_key": object_key,
                "error": None,
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = f"S3 error ({error_code}) for '{object_key}': {e.response['Error']['Message']}"
            logger.error(f"[OBJECT_STORAGE] {error_msg}")
            return {
                "success": False,
                "data": None,
                "content_type": None,
                "size_bytes": 0,
                "object_key": object_key,
                "error": error_msg,
            }
        except EndpointConnectionError as e:
            error_msg = f"Connection error for '{object_key}': {str(e)}"
            logger.error(f"[OBJECT_STORAGE] {error_msg}")
            return {
                "success": False,
                "data": None,
                "content_type": None,
                "size_bytes": 0,
                "object_key": object_key,
                "error": error_msg,
            }
        except Exception as e:
            error_msg = f"Unexpected error downloading '{object_key}': {str(e)}"
            logger.error(f"[OBJECT_STORAGE] {error_msg}", exc_info=True)
            return {
                "success": False,
                "data": None,
                "content_type": None,
                "size_bytes": 0,
                "object_key": object_key,
                "error": error_msg,
            }

    def download_multiple(
        self,
        object_keys: List[str],
        bucket: Optional[str] = None,
        max_workers: int = 3,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Download multiple objects concurrently.
        Since typical count is 1-5 files, uses ThreadPoolExecutor for speed.

        Args:
            object_keys: List of object keys to download.
            bucket: Override bucket name.
            max_workers: Max concurrent downloads (default 3).

        Returns:
            Dict mapping each object_key to its download result.
        """
        results = {}

        if not object_keys:
            return results

        # For 1-2 files, sequential is fine. For 3+, use concurrency.
        if len(object_keys) <= 2:
            for key in object_keys:
                results[key] = self.download_as_base64(key, bucket)
        else:
            with ThreadPoolExecutor(max_workers=min(max_workers, len(object_keys))) as executor:
                future_to_key = {
                    executor.submit(self.download_as_base64, key, bucket): key
                    for key in object_keys
                }
                for future in as_completed(future_to_key):
                    key = future_to_key[future]
                    try:
                        results[key] = future.result()
                    except Exception as e:
                        results[key] = {
                            "success": False,
                            "data": None,
                            "content_type": None,
                            "size_bytes": 0,
                            "object_key": key,
                            "error": str(e),
                        }

        return results

    def _resolve_path(self, hit: dict, path_str: str) -> Any:
        parts = path_str.split(".")
        
        # Determine root: either the hit itself, _source, or fields
        if parts[0] == "_source" or parts[0] == "fields":
            current = hit
        else:
            # Fallback check: first _source, then fields
            current = hit.get("_source")
            if current is None:
                current = hit.get("fields", {})
            
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            if current is None:
                return None
        return current

    def enrich_es_hits_with_objects(
        self,
        hits: List[dict],
        mapping_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Enrich Elasticsearch hit results by downloading referenced objects.

        For each hit, looks at the configured file_paths fields,
        downloads the objects, and injects base64 data into the source.

        Args:
            hits: List of ES hit dicts (each with "_source", "_index", etc.)
            mapping_config: The object_storage_mapping from RequestType.

        Returns:
            {
                "enriched_hits": [...],
                "stats": {
                    "total_files_requested": N,
                    "total_files_downloaded": N,
                    "total_size_bytes": N,
                    "failed_downloads": N,
                    "download_time_ms": N
                }
            }
        """
        file_paths_fields = mapping_config.get("file_paths", [])
        bucket_field = mapping_config.get("bucket_field", None)
        base_prefix = mapping_config.get("base_prefix", "")
        allowed_extensions = mapping_config.get("allowed_extensions", [])

        if not file_paths_fields:
            logger.warning("[OBJECT_STORAGE] No file_paths configured in object_storage_mapping")
            return {"enriched_hits": hits, "stats": self._empty_stats()}

        # Collect all object keys to download
        download_tasks = []  # [(hit_index, field_name, object_key, bucket)]
        for idx, hit in enumerate(hits):
            hit_bucket = self._resolve_path(hit, bucket_field) if bucket_field else None

            for field in file_paths_fields:
                raw_path = self._resolve_path(hit, field)
                if not raw_path:
                    continue

                # Handle both single path (string) and multiple paths (list)
                paths = raw_path if isinstance(raw_path, list) else [raw_path]
                for path in paths:
                    if not isinstance(path, str) or not path.strip():
                        continue

                    # Check allowed extensions
                    if allowed_extensions:
                        ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
                        if ext and ext not in [e.lower() for e in allowed_extensions]:
                            logger.info(f"[OBJECT_STORAGE] Skipping '{path}': extension '{ext}' not in allowed list")
                            continue

                    # Apply base prefix
                    object_key = f"{base_prefix}{path}" if base_prefix and not path.startswith(base_prefix) else path

                    download_tasks.append((idx, field, object_key, hit_bucket))

        # Download all objects
        start_time = time()
        unique_keys = list({t[2] for t in download_tasks})
        download_results = self.download_multiple(unique_keys, bucket=None)

        # For tasks with custom bucket, download separately
        custom_bucket_tasks = [(t[2], t[3]) for t in download_tasks if t[3]]
        for key, bucket in custom_bucket_tasks:
            if key not in download_results or not download_results[key]["success"]:
                download_results[key] = self.download_as_base64(key, bucket)

        download_time_ms = int((time() - start_time) * 1000)

        # Inject results into hits
        stats = {
            "total_files_requested": len(download_tasks),
            "total_files_downloaded": 0,
            "total_size_bytes": 0,
            "failed_downloads": 0,
            "download_time_ms": download_time_ms,
        }

        for idx, field, object_key, _ in download_tasks:
            result = download_results.get(object_key, {})
            # Inject into _source if it exists, otherwise into fields, or create _source
            if "_source" in hits[idx]:
                target = hits[idx]["_source"]
            elif "fields" in hits[idx]:
                target = hits[idx]["fields"]
            else:
                hits[idx]["_source"] = {}
                target = hits[idx]["_source"]

            if result.get("success"):
                target[f"{field}_base64"] = result["data"]
                target[f"{field}_content_type"] = result["content_type"]
                target[f"{field}_size_bytes"] = result["size_bytes"]
                
                # Remove the original file path to save bandwidth
                if field in target:
                    del target[field]
                    
                stats["total_files_downloaded"] += 1
                stats["total_size_bytes"] += result["size_bytes"]
            else:
                target[f"{field}_base64"] = None
                target[f"{field}_error"] = result.get("error", "Download failed")
                stats["failed_downloads"] += 1

        return {
            "enriched_hits": hits,
            "stats": stats,
        }

    def test_connection(self) -> tuple:
        """
        Test connection to the object storage by listing buckets.

        Returns:
            (success: bool, message: str)
        """
        try:
            response = self.client.list_buckets()
            bucket_names = [b["Name"] for b in response.get("Buckets", [])]
            bucket_exists = self.default_bucket in bucket_names

            if bucket_exists:
                msg = (
                    f"Connected successfully. "
                    f"Found {len(bucket_names)} bucket(s). "
                    f"Default bucket '{self.default_bucket}' exists."
                )
            else:
                msg = (
                    f"Connected successfully. "
                    f"Found {len(bucket_names)} bucket(s): {', '.join(bucket_names[:5])}. "
                    f"WARNING: Default bucket '{self.default_bucket}' NOT found!"
                )

            return (True, msg)

        except EndpointConnectionError as e:
            return (False, f"Connection failed: {str(e)}")
        except ClientError as e:
            return (False, f"Auth error: {e.response['Error']['Message']}")
        except Exception as e:
            return (False, f"Unexpected error: {str(e)}")

    @staticmethod
    def _empty_stats() -> dict:
        return {
            "total_files_requested": 0,
            "total_files_downloaded": 0,
            "total_size_bytes": 0,
            "failed_downloads": 0,
            "download_time_ms": 0,
        }
