"""Runs endpoints for listing and viewing ingestion runs."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.index import Index
from app.models.ingestion_run import IngestionRun, IngestionStatus
from app.models.input import Input
from app.models.output import Output
from app.models.props import Props
from app.models.serverclass import Serverclass
from app.models.stanza import Stanza
from app.models.transform import Transform
from app.schemas.index import IndexListResponse, IndexResponse
from app.schemas.ingestion_run import (
    IngestionRunListResponse,
    IngestionRunParseResponse,
    IngestionRunResponse,
    IngestionRunStatusResponse,
    IngestionRunStatusUpdate,
    IngestionRunSummaryResponse,
)
from app.schemas.input import InputListResponse, InputResponse
from app.schemas.output import OutputListResponse, OutputResponse
from app.schemas.props import PropsListResponse, PropsResponse
from app.schemas.serverclass import ServerclassListResponse, ServerclassResponse
from app.schemas.transform import TransformListResponse, TransformResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_run_or_404(db: Session, run_id: int, context: str = "run") -> IngestionRun:
    """Get a run by ID or raise 404.

    Args:
        db: Database session
        run_id: Run ID to fetch
        context: Context string for error messages

    Returns:
        IngestionRun: The requested run

    Raises:
        HTTPException: 400 if invalid run_id, 404 if not found
    """
    # Validate run_id is positive
    if run_id < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid run_id: {run_id}. Must be a positive integer.",
        )

    # Query for the run
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()

    if not run:
        logger.warning(f"Run not found for {context}: run_id={run_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id {run_id} not found",
        )

    return run


def _extract_summary_from_metrics(metrics: dict | None) -> dict | None:
    """Extract summary data from run metrics.

    Args:
        metrics: Run metrics dictionary

    Returns:
        dict | None: Summary with parsed counts, or None if no metrics
    """
    if not metrics:
        return None

    return {
        "files_parsed": metrics.get("files_parsed", 0),
        "stanzas_created": metrics.get("stanzas_created", 0),
        "typed_projections": metrics.get("typed_projections", {}),
        "parse_errors": metrics.get("parse_errors", 0),
        "duration_seconds": metrics.get("duration_seconds", 0),
    }


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

    # Get run or raise 404
    run = _get_run_or_404(db, run_id, context="status")

    # Extract summary from metrics if available
    summary = _extract_summary_from_metrics(run.metrics)

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

    if (
        status_update.status in [IngestionStatus.COMPLETE, IngestionStatus.FAILED]
        and not run.completed_at
    ):
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


@router.post(
    "/runs/{run_id}/parse",
    response_model=IngestionRunParseResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_parse(
    run_id: int,
    db: Session = Depends(get_db),
) -> IngestionRunParseResponse:
    """Trigger background parsing job for an ingestion run.

    Enqueues a Celery task to parse configuration files for this run.
    The task extracts .conf files from the uploaded archive, parses them,
    and persists stanzas and typed projections to the database.

    This endpoint is idempotent - if the run has already been parsed or is
    currently parsing, it returns the existing task information without
    creating a duplicate job.

    Args:
        run_id: Unique identifier of the ingestion run
        db: Database session

    Returns:
        IngestionRunParseResponse: Task ID and status information

    Raises:
        HTTPException: 404 if run not found, 400 if invalid run_id or
                      run is not in a valid state for parsing
    """
    logger.info(f"Triggering parse for run_id={run_id}")

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

    # Check if run is already complete (idempotent handling)
    if run.status == IngestionStatus.COMPLETE:
        logger.info(
            f"Run {run_id} already complete, returning existing task_id",
            extra={"run_id": run_id, "task_id": run.task_id},
        )
        return IngestionRunParseResponse(
            run_id=run.id,
            status=run.status,
            task_id=run.task_id or "completed",
            message=f"Run already completed. Task ID: {run.task_id or 'N/A'}",
        )

    # Check if run is already parsing or normalized
    if run.status in [IngestionStatus.PARSING, IngestionStatus.NORMALIZED]:
        logger.info(
            f"Run {run_id} already in progress (status={run.status}), returning existing task_id",
            extra={"run_id": run_id, "task_id": run.task_id, "status": run.status},
        )
        return IngestionRunParseResponse(
            run_id=run.id,
            status=run.status,
            task_id=run.task_id or "in-progress",
            message=f"Parse job already in progress. Task ID: {run.task_id or 'N/A'}",
        )

    # Check if run is in stored status (ready for parsing)
    # Also allow pending and failed status to be re-parsed
    if run.status not in [
        IngestionStatus.STORED,
        IngestionStatus.PENDING,
        IngestionStatus.FAILED,
    ]:
        logger.warning(
            f"Run {run_id} in invalid status for parsing: {run.status}",
            extra={"run_id": run_id, "status": run.status},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Run status '{run.status.value}' is not valid for parsing. "
            f"Expected: stored, pending, or failed.",
        )

    # Import worker task
    from app.worker.tasks import parse_run

    # Enqueue parse task
    try:
        task = parse_run.delay(run_id)
        task_id = task.id

        logger.info(
            f"Enqueued parse task for run {run_id}",
            extra={"run_id": run_id, "task_id": task_id},
        )

        # Update run status to parsing and store task_id
        run.status = IngestionStatus.PARSING
        run.task_id = task_id
        run.error_message = None  # Clear any previous errors
        run.error_traceback = None

        from datetime import datetime

        run.started_at = datetime.utcnow()
        run.last_heartbeat = datetime.utcnow()

        db.commit()

        logger.info(
            f"Updated run {run_id} status to PARSING with task_id {task_id}",
            extra={"run_id": run_id, "task_id": task_id},
        )

        return IngestionRunParseResponse(
            run_id=run.id,
            status=run.status,
            task_id=task_id,
            message=f"Parse job enqueued successfully. Task ID: {task_id}",
        )

    except Exception as e:
        logger.error(
            f"Failed to enqueue parse task for run {run_id}: {e}",
            exc_info=True,
            extra={"run_id": run_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enqueue parse task: {str(e)}",
        ) from e


@router.get("/runs/{run_id}/parse-status", response_model=IngestionRunStatusResponse)
async def get_parse_status(
    run_id: int,
    db: Session = Depends(get_db),
) -> IngestionRunStatusResponse:
    """Get parse status for a specific ingestion run.

    This endpoint is optimized for frontend polling to track parse progress.
    Returns current parse status, error details if any, and summary metrics.

    Parse status lifecycle: stored → parsing → normalized → complete
                                           ↓
                                        failed

    Args:
        run_id: Unique identifier of the ingestion run
        db: Database session

    Returns:
        IngestionRunStatusResponse: Parse status, error message, and summary

    Raises:
        HTTPException: 404 if run not found, 400 if invalid run_id
    """
    logger.info(f"Fetching parse status for run_id={run_id}")

    # Get run or raise 404
    run = _get_run_or_404(db, run_id, context="parse status")

    # Extract summary from metrics if available
    summary = _extract_summary_from_metrics(run.metrics)

    # Log status transitions for monitoring
    logger.info(
        f"Parse status for run {run_id}: {run.status}",
        extra={
            "run_id": run_id,
            "status": run.status.value,
            "has_error": run.error_message is not None,
            "files_parsed": summary.get("files_parsed", 0) if summary else 0,
        },
    )

    return IngestionRunStatusResponse(
        run_id=run.id,
        status=run.status,
        error_message=run.error_message,
        summary=summary,
    )


@router.get("/runs/{run_id}/inputs", response_model=InputListResponse)
async def list_run_inputs(
    run_id: int,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    per_page: Annotated[int, Query(ge=1, le=100, description="Results per page")] = 50,
    app: Annotated[str | None, Query(description="Filter by app name")] = None,
    scope: Annotated[
        str | None, Query(description="Filter by scope (default/local)")
    ] = None,
    layer: Annotated[
        str | None, Query(description="Filter by layer (system/app)")
    ] = None,
    stanza_type: Annotated[
        str | None, Query(description="Filter by stanza type")
    ] = None,
    index: Annotated[str | None, Query(description="Filter by index")] = None,
    db: Session = Depends(get_db),
) -> InputListResponse:
    """List inputs for a specific ingestion run with pagination and filtering.

    Args:
        run_id: Unique identifier of the ingestion run
        page: Page number (1-indexed)
        per_page: Number of results per page (max 100)
        app: Optional filter by app name
        scope: Optional filter by scope
        layer: Optional filter by layer
        stanza_type: Optional filter by stanza type
        index: Optional filter by index
        db: Database session

    Returns:
        InputListResponse: Paginated list of inputs

    Raises:
        HTTPException: 404 if run not found, 400 if invalid run_id
    """
    logger.info(f"Listing inputs for run_id={run_id}: page={page}, per_page={per_page}")

    # Validate run_id is positive
    if run_id < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid run_id: {run_id}. Must be a positive integer.",
        )

    # Verify run exists
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    if not run:
        logger.warning(f"Run not found: run_id={run_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id {run_id} not found",
        )

    # Build query with filters
    query = db.query(Input).filter(Input.run_id == run_id)

    if app is not None:
        query = query.filter(Input.app == app)
    if scope is not None:
        query = query.filter(Input.scope == scope)
    if layer is not None:
        query = query.filter(Input.layer == layer)
    if stanza_type is not None:
        query = query.filter(Input.stanza_type == stanza_type)
    if index is not None:
        query = query.filter(Input.index == index)

    # Get total count
    total = query.count()

    # Calculate offset and get paginated results
    offset = (page - 1) * per_page
    inputs = query.order_by(Input.id).offset(offset).limit(per_page).all()

    logger.info(f"Found {len(inputs)} inputs (total: {total})")

    return InputListResponse(
        inputs=[InputResponse.model_validate(inp) for inp in inputs],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/runs/{run_id}/props", response_model=PropsListResponse)
async def list_run_props(
    run_id: int,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    per_page: Annotated[int, Query(ge=1, le=100, description="Results per page")] = 50,
    target: Annotated[
        str | None, Query(description="Filter by target (sourcetype/source)")
    ] = None,
    db: Session = Depends(get_db),
) -> PropsListResponse:
    """List props for a specific ingestion run with pagination and filtering.

    Args:
        run_id: Unique identifier of the ingestion run
        page: Page number (1-indexed)
        per_page: Number of results per page (max 100)
        target: Optional filter by target
        db: Database session

    Returns:
        PropsListResponse: Paginated list of props

    Raises:
        HTTPException: 404 if run not found, 400 if invalid run_id
    """
    logger.info(f"Listing props for run_id={run_id}: page={page}, per_page={per_page}")

    # Validate run_id is positive
    if run_id < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid run_id: {run_id}. Must be a positive integer.",
        )

    # Verify run exists
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    if not run:
        logger.warning(f"Run not found: run_id={run_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id {run_id} not found",
        )

    # Build query with filters
    query = db.query(Props).filter(Props.run_id == run_id)

    if target is not None:
        query = query.filter(Props.target == target)

    # Get total count
    total = query.count()

    # Calculate offset and get paginated results
    offset = (page - 1) * per_page
    props = query.order_by(Props.id).offset(offset).limit(per_page).all()

    logger.info(f"Found {len(props)} props (total: {total})")

    return PropsListResponse(
        props=[PropsResponse.model_validate(p) for p in props],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/runs/{run_id}/transforms", response_model=TransformListResponse)
async def list_run_transforms(
    run_id: int,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    per_page: Annotated[int, Query(ge=1, le=100, description="Results per page")] = 50,
    name: Annotated[str | None, Query(description="Filter by transform name")] = None,
    db: Session = Depends(get_db),
) -> TransformListResponse:
    """List transforms for a specific ingestion run with pagination and filtering.

    Args:
        run_id: Unique identifier of the ingestion run
        page: Page number (1-indexed)
        per_page: Number of results per page (max 100)
        name: Optional filter by transform name
        db: Database session

    Returns:
        TransformListResponse: Paginated list of transforms

    Raises:
        HTTPException: 404 if run not found, 400 if invalid run_id
    """
    logger.info(
        f"Listing transforms for run_id={run_id}: page={page}, per_page={per_page}"
    )

    # Validate run_id is positive
    if run_id < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid run_id: {run_id}. Must be a positive integer.",
        )

    # Verify run exists
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    if not run:
        logger.warning(f"Run not found: run_id={run_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id {run_id} not found",
        )

    # Build query with filters
    query = db.query(Transform).filter(Transform.run_id == run_id)

    if name is not None:
        query = query.filter(Transform.name == name)

    # Get total count
    total = query.count()

    # Calculate offset and get paginated results
    offset = (page - 1) * per_page
    transforms = query.order_by(Transform.id).offset(offset).limit(per_page).all()

    logger.info(f"Found {len(transforms)} transforms (total: {total})")

    return TransformListResponse(
        transforms=[TransformResponse.model_validate(t) for t in transforms],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/runs/{run_id}/indexes", response_model=IndexListResponse)
async def list_run_indexes(
    run_id: int,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    per_page: Annotated[int, Query(ge=1, le=100, description="Results per page")] = 50,
    name: Annotated[str | None, Query(description="Filter by index name")] = None,
    db: Session = Depends(get_db),
) -> IndexListResponse:
    """List indexes for a specific ingestion run with pagination and filtering.

    Args:
        run_id: Unique identifier of the ingestion run
        page: Page number (1-indexed)
        per_page: Number of results per page (max 100)
        name: Optional filter by index name
        db: Database session

    Returns:
        IndexListResponse: Paginated list of indexes

    Raises:
        HTTPException: 404 if run not found, 400 if invalid run_id
    """
    logger.info(
        f"Listing indexes for run_id={run_id}: page={page}, per_page={per_page}"
    )

    # Validate run_id is positive
    if run_id < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid run_id: {run_id}. Must be a positive integer.",
        )

    # Verify run exists
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    if not run:
        logger.warning(f"Run not found: run_id={run_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id {run_id} not found",
        )

    # Build query with filters
    query = db.query(Index).filter(Index.run_id == run_id)

    if name is not None:
        query = query.filter(Index.name == name)

    # Get total count
    total = query.count()

    # Calculate offset and get paginated results
    offset = (page - 1) * per_page
    indexes = query.order_by(Index.id).offset(offset).limit(per_page).all()

    logger.info(f"Found {len(indexes)} indexes (total: {total})")

    return IndexListResponse(
        indexes=[IndexResponse.model_validate(idx) for idx in indexes],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/runs/{run_id}/outputs", response_model=OutputListResponse)
async def list_run_outputs(
    run_id: int,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    per_page: Annotated[int, Query(ge=1, le=100, description="Results per page")] = 50,
    group_name: Annotated[
        str | None, Query(description="Filter by output group name")
    ] = None,
    db: Session = Depends(get_db),
) -> OutputListResponse:
    """List outputs for a specific ingestion run with pagination and filtering.

    Args:
        run_id: Unique identifier of the ingestion run
        page: Page number (1-indexed)
        per_page: Number of results per page (max 100)
        group_name: Optional filter by output group name
        db: Database session

    Returns:
        OutputListResponse: Paginated list of outputs

    Raises:
        HTTPException: 404 if run not found, 400 if invalid run_id
    """
    logger.info(
        f"Listing outputs for run_id={run_id}: page={page}, per_page={per_page}"
    )

    # Validate run_id is positive
    if run_id < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid run_id: {run_id}. Must be a positive integer.",
        )

    # Verify run exists
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    if not run:
        logger.warning(f"Run not found: run_id={run_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id {run_id} not found",
        )

    # Build query with filters
    query = db.query(Output).filter(Output.run_id == run_id)

    if group_name is not None:
        query = query.filter(Output.group_name == group_name)

    # Get total count
    total = query.count()

    # Calculate offset and get paginated results
    offset = (page - 1) * per_page
    outputs = query.order_by(Output.id).offset(offset).limit(per_page).all()

    logger.info(f"Found {len(outputs)} outputs (total: {total})")

    return OutputListResponse(
        outputs=[OutputResponse.model_validate(out) for out in outputs],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/runs/{run_id}/serverclasses", response_model=ServerclassListResponse)
async def list_run_serverclasses(
    run_id: int,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    per_page: Annotated[int, Query(ge=1, le=100, description="Results per page")] = 50,
    name: Annotated[str | None, Query(description="Filter by serverclass name")] = None,
    app: Annotated[str | None, Query(description="Filter by app name")] = None,
    scope: Annotated[
        str | None, Query(description="Filter by scope (default/local)")
    ] = None,
    layer: Annotated[
        str | None, Query(description="Filter by layer (system/app)")
    ] = None,
    db: Session = Depends(get_db),
) -> ServerclassListResponse:
    """List serverclasses for a specific ingestion run with pagination and filtering.

    Args:
        run_id: Unique identifier of the ingestion run
        page: Page number (1-indexed)
        per_page: Number of results per page (max 100)
        name: Optional filter by serverclass name
        app: Optional filter by app name
        scope: Optional filter by scope
        layer: Optional filter by layer
        db: Database session

    Returns:
        ServerclassListResponse: Paginated list of serverclasses

    Raises:
        HTTPException: 404 if run not found, 400 if invalid run_id
    """
    logger.info(
        f"Listing serverclasses for run_id={run_id}: page={page}, per_page={per_page}"
    )

    # Validate run_id is positive
    if run_id < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid run_id: {run_id}. Must be a positive integer.",
        )

    # Verify run exists
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    if not run:
        logger.warning(f"Run not found: run_id={run_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id {run_id} not found",
        )

    # Build query with filters
    query = db.query(Serverclass).filter(Serverclass.run_id == run_id)

    if name is not None:
        query = query.filter(Serverclass.name == name)
    if app is not None:
        query = query.filter(Serverclass.app == app)
    if scope is not None:
        query = query.filter(Serverclass.scope == scope)
    if layer is not None:
        query = query.filter(Serverclass.layer == layer)

    # Get total count
    total = query.count()

    # Calculate offset and get paginated results
    offset = (page - 1) * per_page
    serverclasses = query.order_by(Serverclass.id).offset(offset).limit(per_page).all()

    logger.info(f"Found {len(serverclasses)} serverclasses (total: {total})")

    return ServerclassListResponse(
        serverclasses=[ServerclassResponse.model_validate(sc) for sc in serverclasses],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/runs/{run_id}/summary", response_model=IngestionRunSummaryResponse)
async def get_run_summary(
    run_id: int,
    db: Session = Depends(get_db),
) -> IngestionRunSummaryResponse:
    """Get entity count summary for a specific ingestion run.

    Returns counts of all parsed entities including stanzas and typed
    projections (inputs, props, transforms, indexes, outputs, serverclasses).
    Useful for frontend summary panels showing parsing progress and results.

    Args:
        run_id: Unique identifier of the ingestion run
        db: Database session

    Returns:
        IngestionRunSummaryResponse: Entity counts and status

    Raises:
        HTTPException: 404 if run not found, 400 if invalid run_id
    """
    logger.info(f"Fetching summary for run_id={run_id}")

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

    # Query counts for each entity type
    stanzas_count = db.query(Stanza).filter(Stanza.run_id == run_id).count()
    inputs_count = db.query(Input).filter(Input.run_id == run_id).count()
    props_count = db.query(Props).filter(Props.run_id == run_id).count()
    transforms_count = db.query(Transform).filter(Transform.run_id == run_id).count()
    indexes_count = db.query(Index).filter(Index.run_id == run_id).count()
    outputs_count = db.query(Output).filter(Output.run_id == run_id).count()
    serverclasses_count = (
        db.query(Serverclass).filter(Serverclass.run_id == run_id).count()
    )

    logger.info(
        f"Summary for run {run_id}: "
        f"stanzas={stanzas_count}, inputs={inputs_count}, props={props_count}, "
        f"transforms={transforms_count}, indexes={indexes_count}, "
        f"outputs={outputs_count}, serverclasses={serverclasses_count}"
    )

    return IngestionRunSummaryResponse(
        run_id=run.id,
        status=run.status,
        stanzas=stanzas_count,
        inputs=inputs_count,
        props=props_count,
        transforms=transforms_count,
        indexes=indexes_count,
        outputs=outputs_count,
        serverclasses=serverclasses_count,
    )
