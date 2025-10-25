"""Worker status and monitoring endpoints."""

import logging
from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.ingestion_run import IngestionRun
from app.schemas.ingestion_run import IngestionRunResponse
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


@router.get("/worker/runs/{run_id}/status", response_model=IngestionRunResponse)
async def get_run_job_status(
    run_id: int,
    db: Session = Depends(get_db),
) -> IngestionRunResponse:
    """Get job status and error details for a specific run.

    This endpoint provides detailed information about the job execution,
    including retry count, error messages, and execution metrics.

    Args:
        run_id: Ingestion run ID
        db: Database session

    Returns:
        IngestionRunResponse: Run details with job status and errors

    Raises:
        HTTPException: 404 if run not found
    """
    logger.info(f"Fetching job status for run_id={run_id}")

    # Query for the run
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()

    if not run:
        logger.warning(f"Run not found: run_id={run_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id {run_id} not found",
        )

    logger.info(
        f"Found run {run_id}: status={run.status}, retry_count={run.retry_count}",
        extra={
            "run_id": run_id,
            "status": run.status,
            "retry_count": run.retry_count,
            "has_error": bool(run.error_message),
        },
    )

    return IngestionRunResponse.model_validate(run)


@router.get("/worker/metrics")
async def get_worker_metrics(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get worker and job execution metrics.

    Returns aggregated metrics about job execution, including:
    - Total jobs by status
    - Average retry count
    - Average execution duration
    - Recent failure rate

    Args:
        db: Database session

    Returns:
        dict: Aggregated metrics
    """
    from sqlalchemy import func

    from app.models.ingestion_run import IngestionStatus

    try:
        # Get job counts by status
        status_counts = (
            db.query(IngestionRun.status, func.count(IngestionRun.id))
            .group_by(IngestionRun.status)
            .all()
        )

        # Get retry statistics
        retry_stats = db.query(
            func.avg(IngestionRun.retry_count).label("avg_retries"),
            func.max(IngestionRun.retry_count).label("max_retries"),
        ).first()

        # Get failed runs with error details
        failed_runs = (
            db.query(IngestionRun)
            .filter(IngestionRun.status == IngestionStatus.FAILED)
            .order_by(IngestionRun.completed_at.desc())
            .limit(10)
            .all()
        )

        # Calculate average duration for completed runs
        completed_runs = (
            db.query(IngestionRun)
            .filter(IngestionRun.status == IngestionStatus.COMPLETE)
            .filter(IngestionRun.metrics.isnot(None))
            .all()
        )

        avg_duration = 0.0
        if completed_runs:
            durations = [
                run.metrics.get("duration_seconds", 0)
                for run in completed_runs
                if run.metrics
            ]
            avg_duration = sum(durations) / len(durations) if durations else 0.0

        return {
            "status_counts": {status.value: count for status, count in status_counts},
            "retry_stats": {
                "avg_retries": float(retry_stats.avg_retries or 0),
                "max_retries": retry_stats.max_retries or 0,
            },
            "avg_duration_seconds": avg_duration,
            "recent_failures": [
                {
                    "run_id": run.id,
                    "error_message": run.error_message,
                    "retry_count": run.retry_count,
                    "completed_at": run.completed_at.isoformat()
                    if run.completed_at
                    else None,
                }
                for run in failed_runs
            ],
        }

    except Exception as e:
        logger.error(f"Failed to get worker metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve worker metrics: {str(e)}",
        ) from e
