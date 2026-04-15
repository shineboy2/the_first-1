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
    beat_scheduler="celery.beat:PersistentScheduler",
    beat_schedule={
        # EXPORTERS (to Response Network)
        # Export pending requests every 10 seconds
        "export-pending-requests-every-10s": {
            "task": "workers.tasks.export_requests.export_pending_requests",
            "schedule": 10.0,
        },
        
        # IMPORTERS (from Response Network)
        # Import settings from response network every 10 seconds
        "import-settings-every-10s": {
            "task": "workers.tasks.settings_importer.import_settings_from_response_network",
            "schedule": 10.0,
        },
        # Import users from response network every 60 seconds (only if changed)
        "import-users-every-60s": {
            "task": "workers.tasks.users_importer.import_users_from_response_network",
            "schedule": 60.0,
        },
        # Import results from response network every 10 seconds
        "import-results-every-10s": {
            "task": "workers.tasks.results_importer.import_results_from_response_network",
            "schedule": 10.0,
        },
        # Cleanup old files daily
        "cleanup-old-files-daily": {
            "task": "cleanup.cleanup_old_files",
            "schedule": 86400.0,  # هر 24 ساعت (روزانه)
        },
    },
)

# Auto-discover tasks from this package
celery_app.autodiscover_tasks(["workers.tasks"], force=True)

# Import tasks explicitly to ensure they are registered
from workers.tasks import settings_importer  # noqa
from workers.tasks import export_requests  # noqa
from workers.tasks import users_importer  # noqa
from workers.tasks import results_importer  # noqa
from workers.tasks import cleanup  # noqa