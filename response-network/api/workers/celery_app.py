from celery import Celery
from core.config import settings

# Initialize celery app
celery_app = Celery(
    "response_network",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Windows-specific configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Ensure tasks stay in queue if worker goes down
    result_expires=3600,  # 1 hour
)

# Auto-discover tasks BEFORE setting beat_schedule
celery_app.autodiscover_tasks(["workers.tasks"], force=True)

# Import all tasks explicitly to ensure they're registered
from workers.tasks.import_requests import import_requests_from_request_network
from workers.tasks.export_results import export_completed_results
from workers.tasks.request_types_exporter import export_request_types_to_request_network
from workers.tasks.access_exporter import export_access_to_request_network

from workers.tasks.system_monitoring import system_health_check
from workers.tasks.execute_query import execute_pending_queries
from workers.tasks.users_exporter import export_users_to_request_network
from workers.tasks.cleanup import cleanup_old_files

# Celery Beat schedule for the Response Network
celery_app.conf.beat_schedule = {
    # Export users to request-network every 5 minutes
    "export-users-every-5min": {
        "task": "workers.tasks.users_exporter.export_users_to_request_network",
        "schedule": 300.0,  # هر 300 ثانیه (5 دقیقه)
    },
    # Import requests from request-network every 10 seconds (polling)
    "import-requests-from-request-network": {
        "task": "workers.tasks.import_requests.import_requests_from_request_network",
        "schedule": 10.0,  # هر 10 ثانیه
    },
    # Export results to request-network every 10 seconds
    "export-results-to-request-network": {
        "task": "workers.tasks.export_results.export_completed_results",
        "schedule": 10.0,  # هر 10 ثانیه
    },
    # Export request types to request-network every 60 seconds
    "export-request-types-every-minute": {
        "task": "workers.tasks.request_types_exporter.export_request_types_to_request_network",
        "schedule": 60.0,
    },

    # System monitoring every 5 minutes
    # "system-monitoring-every-5min": {
    #     "task": "workers.tasks.system_monitoring.system_health_check",
    #     "schedule": 300.0,  # هر 300 ثانیه (5 دقیقه)
    # },
    # Execute pending queries every 10 seconds
    "execute-pending-queries": {
        "task": "workers.tasks.execute_query.execute_pending_queries",
        "schedule": 10.0,
    },
    # Cleanup old files daily at 02:00 AM
    "cleanup-old-files-daily": {
        "task": "cleanup.cleanup_old_files",
        "schedule": 86400.0,  # هر 24 ساعت (روزانه)
    }
}