from celery import Celery
from celery.schedules import crontab
from core.config import settings

# Initialize celery app
celery_app = Celery(
    "request_network",
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
    beat_scheduler="redbeat.RedBeatScheduler",
    redbeat_redis_url=settings.CELERY_BROKER_URL,
    redbeat_key_prefix="redbeat",
    # Initial static schedule is moved to database/redbeat setup script
    # See initialization logic to populate RedBeat
)

from celery.signals import beat_init

@beat_init.connect
def setup_redbeat_tasks(sender, **kwargs):
    from redbeat import RedBeatSchedulerEntry
    
    # Define default tasks
    tasks = [
        ("export-pending-requests", "workers.tasks.export_requests.export_pending_requests", 10.0),
        ("export-audit-logs", "workers.tasks.export_audit_logs.export_audit_logs", 30.0),
        ("import-audit-acks", "workers.tasks.import_audit_acks.import_audit_acks", 30.0),
        ("import-users", "workers.tasks.users_importer.import_users_from_response_network", 60.0),
        ("import-results", "workers.tasks.results_importer.import_results_from_response_network", 10.0),
        ("import-request-types", "workers.tasks.request_types_importer.import_request_types_from_response_network", 300.0),
        ("cleanup-old-files", "workers.tasks.cleanup.cleanup_old_files", 86400.0),
    ]
    
    for name, task, interval in tasks:
        try:
            entry = RedBeatSchedulerEntry(name, task, interval, app=sender.app)
            entry.save()
            print(f"RedBeat: Seeded task {name} with interval {interval}s")
        except Exception as e:
            print(f"RedBeat Error: Failed to seed task {name}: {e}")

# Auto-discover tasks from this package
celery_app.autodiscover_tasks(["workers.tasks"], force=True)

# Import tasks explicitly to ensure they are registered
from workers.tasks import settings_importer  # noqa
from workers.tasks import export_requests  # noqa
from workers.tasks import export_audit_logs  # noqa
from workers.tasks import import_audit_acks  # noqa
from workers.tasks import users_importer  # noqa
from workers.tasks import results_importer  # noqa
from workers.tasks import request_types_importer  # noqa
from workers.tasks import cleanup  # noqa