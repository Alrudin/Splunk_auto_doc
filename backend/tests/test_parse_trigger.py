"""Tests for the POST /runs/{id}/parse endpoint."""

from unittest.mock import MagicMock, patch

from app.models.ingestion_run import IngestionRun, IngestionStatus, IngestionType


class TestParseTriggerEndpoint:
    """Tests for triggering parse jobs on ingestion runs."""

    def test_trigger_parse_success(self, client, db_session):
        """Test successful parse trigger for a run in stored status."""
        # Create a run in stored status
        run = IngestionRun(
            type=IngestionType.INSTANCE_ETC,
            status=IngestionStatus.STORED,
            label="Test Run",
        )
        db_session.add(run)
        db_session.commit()
        run_id = run.id

        # Mock the Celery task
        with patch("app.worker.tasks.parse_run") as mock_task:
            mock_result = MagicMock()
            mock_result.id = "test-task-id-12345"
            mock_task.delay.return_value = mock_result

            # Trigger parse
            response = client.post(f"/v1/runs/{run_id}/parse")

            # Verify response
            assert response.status_code == 202
            data = response.json()
            assert data["run_id"] == run_id
            assert data["status"] == "parsing"
            assert data["task_id"] == "test-task-id-12345"
            assert "enqueued successfully" in data["message"].lower()

            # Verify task was called
            mock_task.delay.assert_called_once_with(run_id)

            # Verify database was updated
            db_session.refresh(run)
            assert run.status == IngestionStatus.PARSING
            assert run.task_id == "test-task-id-12345"
            assert run.started_at is not None
            assert run.last_heartbeat is not None
            assert run.error_message is None

    def test_trigger_parse_nonexistent_run(self, client):
        """Test triggering parse on a non-existent run returns 404."""
        response = client.post("/v1/runs/99999/parse")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_trigger_parse_invalid_run_id(self, client):
        """Test triggering parse with invalid run_id returns 400."""
        response = client.post("/v1/runs/0/parse")

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "invalid run_id" in data["detail"].lower()

    def test_trigger_parse_already_complete(self, client, db_session):
        """Test triggering parse on already completed run is idempotent."""
        # Create a run in complete status
        run = IngestionRun(
            type=IngestionType.INSTANCE_ETC,
            status=IngestionStatus.COMPLETE,
            task_id="original-task-id",
            label="Completed Run",
        )
        db_session.add(run)
        db_session.commit()
        run_id = run.id

        # Trigger parse (should not create new task)
        response = client.post(f"/v1/runs/{run_id}/parse")

        # Should return 202 but not enqueue new task
        assert response.status_code == 202
        data = response.json()
        assert data["run_id"] == run_id
        assert data["status"] == "complete"
        assert data["task_id"] == "original-task-id"
        assert "already completed" in data["message"].lower()

        # Verify database was not changed
        db_session.refresh(run)
        assert run.status == IngestionStatus.COMPLETE
        assert run.task_id == "original-task-id"

    def test_trigger_parse_already_parsing(self, client, db_session):
        """Test triggering parse on run that's already parsing."""
        # Create a run in parsing status
        run = IngestionRun(
            type=IngestionType.INSTANCE_ETC,
            status=IngestionStatus.PARSING,
            task_id="in-progress-task-id",
            label="Parsing Run",
        )
        db_session.add(run)
        db_session.commit()
        run_id = run.id

        # Trigger parse (should not create new task)
        response = client.post(f"/v1/runs/{run_id}/parse")

        # Should return 202 but not enqueue new task
        assert response.status_code == 202
        data = response.json()
        assert data["run_id"] == run_id
        assert data["status"] == "parsing"
        assert data["task_id"] == "in-progress-task-id"
        assert "already in progress" in data["message"].lower()

        # Verify database was not changed
        db_session.refresh(run)
        assert run.status == IngestionStatus.PARSING
        assert run.task_id == "in-progress-task-id"

    def test_trigger_parse_already_normalized(self, client, db_session):
        """Test triggering parse on run that's already normalized."""
        # Create a run in normalized status
        run = IngestionRun(
            type=IngestionType.INSTANCE_ETC,
            status=IngestionStatus.NORMALIZED,
            task_id="normalized-task-id",
            label="Normalized Run",
        )
        db_session.add(run)
        db_session.commit()
        run_id = run.id

        # Trigger parse (should not create new task)
        response = client.post(f"/v1/runs/{run_id}/parse")

        # Should return 202 but not enqueue new task
        assert response.status_code == 202
        data = response.json()
        assert data["run_id"] == run_id
        assert data["status"] == "normalized"
        assert data["task_id"] == "normalized-task-id"
        assert "already in progress" in data["message"].lower()

    def test_trigger_parse_from_pending_status(self, client, db_session):
        """Test triggering parse from pending status is allowed."""
        # Create a run in pending status
        run = IngestionRun(
            type=IngestionType.INSTANCE_ETC,
            status=IngestionStatus.PENDING,
            label="Pending Run",
        )
        db_session.add(run)
        db_session.commit()
        run_id = run.id

        # Mock the Celery task
        with patch("app.worker.tasks.parse_run") as mock_task:
            mock_result = MagicMock()
            mock_result.id = "pending-task-id"
            mock_task.delay.return_value = mock_result

            # Trigger parse
            response = client.post(f"/v1/runs/{run_id}/parse")

            # Verify response
            assert response.status_code == 202
            data = response.json()
            assert data["run_id"] == run_id
            assert data["status"] == "parsing"
            assert data["task_id"] == "pending-task-id"

            # Verify task was called
            mock_task.delay.assert_called_once_with(run_id)

    def test_trigger_parse_from_failed_status(self, client, db_session):
        """Test triggering parse from failed status allows retry."""
        # Create a run in failed status
        run = IngestionRun(
            type=IngestionType.INSTANCE_ETC,
            status=IngestionStatus.FAILED,
            error_message="Previous error",
            error_traceback="Stack trace...",
            label="Failed Run",
        )
        db_session.add(run)
        db_session.commit()
        run_id = run.id

        # Mock the Celery task
        with patch("app.worker.tasks.parse_run") as mock_task:
            mock_result = MagicMock()
            mock_result.id = "retry-task-id"
            mock_task.delay.return_value = mock_result

            # Trigger parse
            response = client.post(f"/v1/runs/{run_id}/parse")

            # Verify response
            assert response.status_code == 202
            data = response.json()
            assert data["run_id"] == run_id
            assert data["status"] == "parsing"
            assert data["task_id"] == "retry-task-id"

            # Verify error was cleared
            db_session.refresh(run)
            assert run.error_message is None
            assert run.error_traceback is None
            assert run.status == IngestionStatus.PARSING

    def test_trigger_parse_response_structure(self, client, db_session):
        """Test that parse trigger response has expected structure."""
        # Create a run
        run = IngestionRun(
            type=IngestionType.INSTANCE_ETC,
            status=IngestionStatus.STORED,
            label="Test Run",
        )
        db_session.add(run)
        db_session.commit()
        run_id = run.id

        # Mock the Celery task
        with patch("app.worker.tasks.parse_run") as mock_task:
            mock_result = MagicMock()
            mock_result.id = "task-12345"
            mock_task.delay.return_value = mock_result

            # Trigger parse
            response = client.post(f"/v1/runs/{run_id}/parse")

            # Verify response structure
            assert response.status_code == 202
            data = response.json()

            # Check all required fields are present
            assert "run_id" in data
            assert "status" in data
            assert "task_id" in data
            assert "message" in data

            # Verify types
            assert isinstance(data["run_id"], int)
            assert isinstance(data["status"], str)
            assert isinstance(data["task_id"], str)
            assert isinstance(data["message"], str)

    def test_trigger_parse_celery_error_handling(self, client, db_session):
        """Test error handling when Celery task fails to enqueue."""
        # Create a run
        run = IngestionRun(
            type=IngestionType.INSTANCE_ETC,
            status=IngestionStatus.STORED,
            label="Test Run",
        )
        db_session.add(run)
        db_session.commit()
        run_id = run.id

        # Mock the Celery task to raise an error
        with patch("app.worker.tasks.parse_run") as mock_task:
            mock_task.delay.side_effect = Exception("Celery connection failed")

            # Trigger parse
            response = client.post(f"/v1/runs/{run_id}/parse")

            # Should return 500 error
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "failed to enqueue" in data["detail"].lower()

    def test_trigger_parse_content_type_json(self, client, db_session):
        """Test that response is JSON."""
        # Create a run
        run = IngestionRun(
            type=IngestionType.INSTANCE_ETC,
            status=IngestionStatus.STORED,
            label="Test Run",
        )
        db_session.add(run)
        db_session.commit()
        run_id = run.id

        # Mock the Celery task
        with patch("app.worker.tasks.parse_run") as mock_task:
            mock_result = MagicMock()
            mock_result.id = "task-id"
            mock_task.delay.return_value = mock_result

            # Trigger parse
            response = client.post(f"/v1/runs/{run_id}/parse")

            # Verify content type
            assert response.headers["content-type"] == "application/json"

    def test_trigger_parse_multiple_runs(self, client, db_session):
        """Test triggering parse on multiple runs independently."""
        # Create multiple runs
        runs = []
        for i in range(3):
            run = IngestionRun(
                type=IngestionType.INSTANCE_ETC,
                status=IngestionStatus.STORED,
                label=f"Test Run {i}",
            )
            db_session.add(run)
            runs.append(run)
        db_session.commit()

        # Mock the Celery task
        with patch("app.worker.tasks.parse_run") as mock_task:
            task_ids = []
            for i, _run in enumerate(runs):
                mock_result = MagicMock()
                mock_result.id = f"task-{i}"
                task_ids.append(mock_result.id)

            mock_task.delay.side_effect = [
                MagicMock(id=f"task-{i}") for i in range(len(runs))
            ]

            # Trigger parse for each run
            for run in runs:
                response = client.post(f"/v1/runs/{run.id}/parse")
                assert response.status_code == 202

            # Verify all tasks were called
            assert mock_task.delay.call_count == len(runs)
