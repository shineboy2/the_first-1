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
    # RedBeat configuration for dynamic scheduling
    redbeat_redis_url=settings.CELERY_BROKER_URL,
    beat_scheduler='redbeat.RedBeatScheduler',
    beat_max_loop_interval=5,
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
from workers.tasks.file_request_sender import send_file_request
from workers.tasks.file_request_poller import poll_file_responses

from celery.signals import beat_init

@beat_init.connect
def setup_redbeat_tasks(sender, **kwargs):
    from redbeat import RedBeatSchedulerEntry
    
    # Define default tasks
    tasks = [
        ("export-users-every-5min", "workers.tasks.users_exporter.export_users_to_request_network", 300.0),
        ("import-requests-from-request-network", "workers.tasks.import_requests.import_requests_from_request_network", 10.0),
        ("export-results-to-request-network", "workers.tasks.export_results.export_completed_results", 10.0),
        ("import-audit-logs", "workers.tasks.import_audit_logs.import_audit_logs", 30.0),
        ("export-request-types-every-minute", "workers.tasks.request_types_exporter.export_request_types_to_request_network", 60.0),
        ("execute-pending-queries", "workers.tasks.execute_query.execute_pending_queries", 10.0),
        ("cleanup-old-files-daily", "cleanup.cleanup_old_files", 86400.0),
        ("poll-file-responses", "workers.tasks.file_request_poller.poll_file_responses", 60.0),
    ]
    
    for name, task, interval in tasks:
        try:
            entry = RedBeatSchedulerEntry(name, task, interval, app=sender.app)
            entry.save()
            print(f"RedBeat: Seeded task {name} with interval {interval}s")
        except Exception as e:
            print(f"RedBeat Error: Failed to seed task {name}: {e}")