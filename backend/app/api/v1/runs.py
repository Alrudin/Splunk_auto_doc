"""Runs endpoints for listing and viewing ingestion runs."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.ingestion_run import IngestionRun
from app.schemas.ingestion_run import IngestionRunListResponse, IngestionRunResponse

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
