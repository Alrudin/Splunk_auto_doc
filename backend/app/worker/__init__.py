"""Worker module for background task processing."""

from app.worker.celery_app import celery_app

__all__ = ["celery_app"]
