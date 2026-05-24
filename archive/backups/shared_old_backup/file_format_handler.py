import json
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Generator, Union, Optional, Tuple

FILENAME_FORMAT = "{timestamp}_{batch_type}_{batch_id}"

class JSONLHandler:
    """
    A utility class to handle reading from and writing to JSONL (JSON Lines) files.
    Each line in a JSONL file is a separate, valid JSON object.
    """

    @staticmethod
    def write_jsonl(data: List[Dict[str, Any]], file_path: Union[str, Path]) -> None:
        """
        Writes a list of dictionaries to a file in JSONL format.

        Args:
            data: A list of dictionaries to write.
            file_path: The path to the output file.
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', encoding='utf-8') as f:
            for record in data:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

    @staticmethod
    def read_jsonl(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Reads a JSONL file and returns a list of dictionaries.

        Args:
            file_path: The path to the JSONL file.

        Returns:
            A list of dictionaries parsed from the file.
        """
        return list(JSONLHandler.stream_read_jsonl(file_path))

    @staticmethod
    def stream_read_jsonl(file_path: Union[str, Path]) -> Generator[Dict[str, Any], None, None]:
        """
        Reads a JSONL file line by line, yielding each parsed JSON object.
        This is memory-efficient for very large files.
        """
        with Path(file_path).open('r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)


class BatchMetadata:
    """
    Handles the creation, reading, and validation of batch metadata files.
    """
    def __init__(self, batch_id: uuid.UUID, batch_type: str, record_count: int, file_path: Path, checksum: str):
        self.batch_id = batch_id
        self.batch_type = batch_type
        self.record_count = record_count
        self.file_path = file_path
        self.checksum = checksum
        self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the metadata to a dictionary."""
        return {
            "batch_id": str(self.batch_id),
            "batch_type": self.batch_type,
            "record_count": self.record_count,
            "file_size_bytes": self.file_path.stat().st_size,
            "checksum_sha256": self.checksum,
            "created_at_utc": self.created_at.isoformat(),
        }

    def write_metadata_file(self) -> Path:
        """Writes the metadata to a .meta file next to the data file."""
        meta_path = self.file_path.with_suffix('.meta')
        with meta_path.open('w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
        return meta_path


def generate_filename(batch_type: str, batch_id: uuid.UUID) -> str:
    """
    Generates a standardized filename for a batch.
    Format: {timestamp}_{batch_type}_{batch_id}.jsonl
    Example: 20250115143000_requests_export_b1e3a5c8-f2d7-4c8e-b1a5-c8f2d74c8e0a.jsonl
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    base_name = FILENAME_FORMAT.format(timestamp=timestamp, batch_type=batch_type, batch_id=str(batch_id))
    return f"{base_name}.jsonl"


def parse_filename(filename: str) -> Optional[Dict[str, str]]:
    """
    Parses a standardized filename to extract its components.
    Returns a dictionary with 'timestamp', 'batch_type', and 'batch_id', or None if format is invalid.
    """
    try:
        base_name = Path(filename).stem
        parts = base_name.split('_')
        if len(parts) < 3:
            return None
        
        return {
            "timestamp": parts[0],
            "batch_type": "_".join(parts[1:-1]), # Handles batch_types with underscores
            "batch_id": parts[-1]
        }
    except (IndexError, ValueError):
        return None

def calculate_checksum(file_path: Union[str, Path]) -> str:
    """Calculates the SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()