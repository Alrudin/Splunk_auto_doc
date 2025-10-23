"""Worker status and monitoring endpoints."""

import logging
from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, status

from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/worker/health")
async def worker_health() -> dict[str, Any]:
    """Check worker health and availability.

    Returns:
        dict: Worker health status including active workers and stats

    Raises:
        HTTPException: If workers are unavailable
    """
    try:
        # Inspect active workers
        inspect = celery_app.control.inspect()

        # Get active workers
        active_workers = inspect.active()

        if not active_workers:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No active workers found",
            )

        # Get worker stats
        stats = inspect.stats()

        # Count total workers
        worker_count = len(active_workers) if active_workers else 0

        # Get active tasks count
        total_active_tasks = (
            sum(len(tasks) for tasks in active_workers.values())
            if active_workers
            else 0
        )

        return {
            "status": "healthy",
            "workers": worker_count,
            "active_tasks": total_active_tasks,
            "worker_names": list(active_workers.keys()) if active_workers else [],
            "stats": stats,
        }

    except Exception as e:
        logger.error(f"Worker health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Worker health check failed: {str(e)}",
        ) from e


@router.get("/worker/tasks/{task_id}")
async def get_task_status(task_id: str) -> dict[str, Any]:
    """Get status of a specific task.

    Args:
        task_id: Celery task ID

    Returns:
        dict: Task status and result information
    """
    try:
        result = AsyncResult(task_id, app=celery_app)

        response = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
        }

        # Include result if task is complete
        if result.ready():
            if result.successful():
                response["result"] = result.result
            else:
                response["error"] = str(result.info)

        return response

    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve task status: {str(e)}",
        ) from e
