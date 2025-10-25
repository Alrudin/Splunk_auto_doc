"""Runs endpoints for listing and viewing ingestion runs."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.ingestion_run import IngestionRun, IngestionStatus
from app.schemas.ingestion_run import (
    IngestionRunListResponse,
    IngestionRunResponse,
    IngestionRunStatusResponse,
    IngestionRunStatusUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/runs", response_model=IngestionRunListResponse)
async def list_runs(
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    per_page: Annotated[int, Query(ge=1, le=100, description="Results per page")] = 50,
    db: Session = Depends(get_db),
) -> IngestionRunListResponse:
    """List all ingestion runs with pagination.

    Returns a paginated list of ingestion runs ordered by created_at descending
    (most recent first).

    Args:
        page: Page number (1-indexed)
        per_page: Number of results per page (max 100)
        db: Database session

    Returns:
        IngestionRunListResponse: Paginated list of runs
    """
    logger.info(f"Listing runs: page={page}, per_page={per_page}")

    # Calculate offset
    offset = (page - 1) * per_page

    # Get total count
    total = db.query(IngestionRun).count()

    # Get paginated runs ordered by created_at descending
    runs = (
        db.query(IngestionRun)
        .order_by(IngestionRun.created_at.desc())
        .offset(offset)
        .limit(per_page)
        .all()
    )

    logger.info(f"Found {len(runs)} runs (total: {total})")

    return IngestionRunListResponse(
        runs=[IngestionRunResponse.model_validate(run) for run in runs],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/runs/{run_id}", response_model=IngestionRunResponse)
async def get_run(
    run_id: int,
    db: Session = Depends(get_db),
) -> IngestionRunResponse:
    """Get details for a specific ingestion run.

    Args:
        run_id: Unique identifier of the ingestion run
        db: Database session

    Returns:
        IngestionRunResponse: Run details

    Raises:
        HTTPException: 404 if run not found, 400 if invalid run_id
    """
    logger.info(f"Fetching run details for run_id={run_id}")

    # Validate run_id is positive
    if run_id < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid run_id: {run_id}. Must be a positive integer.",
        )

    # Query for the run
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()

    if not run:
        logger.warning(f"Run not found: run_id={run_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id {run_id} not found",
        )

    logger.info(f"Found run: {run}")

    return IngestionRunResponse.model_validate(run)


@router.get("/runs/{run_id}/status", response_model=IngestionRunStatusResponse)
async def get_run_status(
    run_id: int,
    db: Session = Depends(get_db),
) -> IngestionRunStatusResponse:
    """Get status for a specific ingestion run.

    Returns current status, error details, and summary metrics.

    Args:
        run_id: Unique identifier of the ingestion run
        db: Database session

    Returns:
        IngestionRunStatusResponse: Status, error, and summary

    Raises:
        HTTPException: 404 if run not found, 400 if invalid run_id
    """
    logger.info(f"Fetching status for run_id={run_id}")

    # Validate run_id is positive
    if run_id < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid run_id: {run_id}. Must be a positive integer.",
        )

    # Query for the run
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()

    if not run:
        logger.warning(f"Run not found: run_id={run_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id {run_id} not found",
        )

    # Extract summary from metrics if available
    summary = None
    if run.metrics:
        summary = {
            "files_parsed": run.metrics.get("files_parsed", 0),
            "stanzas_created": run.metrics.get("stanzas_created", 0),
            "typed_projections": run.metrics.get("typed_projections", {}),
            "parse_errors": run.metrics.get("parse_errors", 0),
            "duration_seconds": run.metrics.get("duration_seconds", 0),
        }

    logger.info(f"Status for run {run_id}: {run.status}")

    return IngestionRunStatusResponse(
        run_id=run.id,
        status=run.status,
        error_message=run.error_message,
        summary=summary,
    )


@router.patch("/runs/{run_id}/status", response_model=IngestionRunStatusResponse)
async def update_run_status(
    run_id: int,
    status_update: IngestionRunStatusUpdate,
    db: Session = Depends(get_db),
) -> IngestionRunStatusResponse:
    """Update status for a specific ingestion run (admin/debug only).

    This endpoint is for debugging and administrative purposes.
    Normal status transitions happen automatically via the worker.

    Args:
        run_id: Unique identifier of the ingestion run
        status_update: New status and optional error message
        db: Database session

    Returns:
        IngestionRunStatusResponse: Updated status

    Raises:
        HTTPException: 404 if run not found, 400 if invalid run_id
    """
    logger.info(
        f"Updating status for run_id={run_id} to {status_update.status}",
        extra={"admin_action": True},
    )

    # Validate run_id is positive
    if run_id < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid run_id: {run_id}. Must be a positive integer.",
        )

    # Query for the run
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()

    if not run:
        logger.warning(f"Run not found: run_id={run_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id {run_id} not found",
        )

    # Update status
    old_status = run.status
    run.status = status_update.status

    # Update error message if provided
    if status_update.error_message is not None:
        run.error_message = status_update.error_message

    # Mark as completed if transitioning to terminal state
    from datetime import datetime

    if status_update.status in [IngestionStatus.COMPLETE, IngestionStatus.FAILED]:
        if not run.completed_at:
            run.completed_at = datetime.utcnow()

    db.commit()

    logger.info(
        f"Updated run {run_id} status: {old_status} → {status_update.status}",
        extra={"admin_action": True},
    )

    # Extract summary from metrics if available
    summary = None
    if run.metrics:
        summary = {
            "files_parsed": run.metrics.get("files_parsed", 0),
            "stanzas_created": run.metrics.get("stanzas_created", 0),
            "typed_projections": run.metrics.get("typed_projections", {}),
            "parse_errors": run.metrics.get("parse_errors", 0),
            "duration_seconds": run.metrics.get("duration_seconds", 0),
        }

    return IngestionRunStatusResponse(
        run_id=run.id,
        status=run.status,
        error_message=run.error_message,
        summary=summary,
    )

