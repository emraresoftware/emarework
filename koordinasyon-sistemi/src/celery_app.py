"""
Celery Task Queue - Background Jobs
Production-ready async task processing
"""
from celery import Celery  # type: ignore
from src.config import settings
import structlog

logger = structlog.get_logger()

# Celery app
app = Celery(
    "hive_coordinator",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Istanbul",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 saat max
    task_soft_time_limit=3000,  # 50 dakika soft limit
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Periyodik görevler (Celery Beat)
    beat_schedule={
        "heartbeat-check-every-5-min": {
            "task": "src.tasks.check_node_health",
            "schedule": 300,  # 5 dakika
        },
        "aggregate-stats-every-30-sec": {
            "task": "src.tasks.aggregate_subtree_stats",
            "schedule": settings.aggregation_interval_sec,
        },
        "cleanup-expired-messages": {
            "task": "src.tasks.cleanup_expired_messages",
            "schedule": 600,  # 10 dakika
        },
        "rebalance-loads-every-10-min": {
            "task": "src.tasks.rebalance_node_loads",
            "schedule": 600,  # 10 dakika
        },
        # ── Emare Ekosistem Görevleri ─────────────────────────────────────────
        "emare-health-check-every-5-min": {
            "task": "src.tasks.emare_health_check",
            "schedule": 300,  # 5 dakika
        },
        "emare-repair-symlinks-every-30-min": {
            "task": "src.tasks.emare_repair_symlinks",
            "schedule": 1800,  # 30 dakika
        },
        "emare-refresh-dosya-yapisi-daily": {
            "task": "src.tasks.emare_refresh_dosya_yapisi",
            "schedule": 86400,  # günlük (24 saat)
        },
    },
)

logger.info("celery_configured", broker=settings.celery_broker_url)
