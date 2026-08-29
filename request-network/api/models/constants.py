from enum import Enum

class RequestState(str, Enum):
    PENDING = "pending"
    EXPORTING = "exporting"
    EXPORTED = "exported"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
