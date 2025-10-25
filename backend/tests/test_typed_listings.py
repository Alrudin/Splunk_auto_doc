"""Tests for typed listing endpoints (inputs, props, transforms, indexes, outputs, serverclasses)."""

import pytest

# Ensure all models are imported first
import tests.ensure_models  # noqa: F401

# Try to import dependencies, skip tests if not available
try:
    from app.api.v1.uploads import get_storage
    from app.core.db import Base, get_db
    from app.main import create_app
    from app.models.index import Index
    from app.models.ingestion_run import IngestionRun, IngestionStatus, IngestionType
    from app.models.input import Input
    from app.models.output import Output
    from app.models.props import Props
    from app.models.serverclass import Serverclass
    from app.models.transform import Transform
    from app.storage import get_storage_backend
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    SKIP_REASON = f"Dependencies not available: {e}"


@pytest.fixture
def test_db():
    """Create a test database."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    # Import models explicitly to ensure they are registered with Base metadata
    import app.models  # noqa: F401
    from app.models.file import File  # noqa: F401
    from app.models.index import Index  # noqa: F401
    from app.models.ingestion_run import IngestionRun  # noqa: F401
    from app.models.input import Input  # noqa: F401
    from app.models.output import Output  # noqa: F401
    from app.models.props import Props  # noqa: F401
    from app.models.serverclass import Serverclass  # noqa: F401
    from app.models.transform import Transform  # noqa: F401

    # Use in-memory SQLite for testing with proper configuration
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        pool_pre_ping=True,
    )

    # Create tables
    Base.metadata.create_all(engine)

    # Verify tables were actually created
    from sqlalchemy import inspect

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "ingestion_runs" not in tables:
        raise RuntimeError(
            f"ingestion_runs table not created. Available tables: {tables}"
        )

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSessionLocal

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def test_storage():
    """Create a test storage backend."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = get_storage_backend(backend_type="local", storage_path=tmpdir)
        yield storage


@pytest.fixture
def client(test_db, test_storage):
    """Create a test client with overridden dependencies."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    app = create_app()

    # Override database dependency
    def override_get_db():
        db = test_db()
        try:
            yield db
        finally:
            db.close()

    # Override storage dependency
    def override_get_storage():
        return test_storage

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage] = override_get_storage

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_run(test_db):
    """Create a sample ingestion run."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    db = test_db()
    run = IngestionRun(
        type=IngestionType.DS_ETC,
        label="Test Run",
        status=IngestionStatus.COMPLETE,
    )
    db.add(run)
    db.commit()
    run_id = run.id
    db.close()
    return run_id


@pytest.mark.database
class TestInputsListEndpoint:
    """Tests for the GET /v1/runs/{id}/inputs endpoint."""

    def test_list_inputs_empty(self, client, sample_run):
        """Test listing inputs when there are none."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        response = client.get(f"/v1/runs/{sample_run}/inputs")

        assert response.status_code == 200
        data = response.json()

        assert data["inputs"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 50

    def test_list_inputs_with_data(self, client, test_db, sample_run):
        """Test listing inputs with actual data."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create test inputs
        db = test_db()
        for i in range(3):
            inp = Input(
                run_id=sample_run,
                source_path=f"/opt/splunk/etc/apps/app{i}/default/inputs.conf",
                stanza_type="monitor://",
                index="main",
                sourcetype=f"test_sourcetype_{i}",
                app=f"app{i}",
                scope="default",
                layer="app",
            )
            db.add(inp)
        db.commit()
        db.close()

        response = client.get(f"/v1/runs/{sample_run}/inputs")

        assert response.status_code == 200
        data = response.json()

        assert len(data["inputs"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1

    def test_list_inputs_pagination(self, client, test_db, sample_run):
        """Test pagination of inputs."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create 5 test inputs
        db = test_db()
        for i in range(5):
            inp = Input(
                run_id=sample_run,
                source_path=f"/opt/splunk/etc/apps/app{i}/default/inputs.conf",
                stanza_type="monitor://",
                index="main",
            )
            db.add(inp)
        db.commit()
        db.close()

        # Test first page with 2 per page
        response = client.get(f"/v1/runs/{sample_run}/inputs?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 5
        assert len(data["inputs"]) == 2
        assert data["page"] == 1
        assert data["per_page"] == 2

    def test_list_inputs_filtering(self, client, test_db, sample_run):
        """Test filtering inputs by various fields."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create test inputs with different properties
        db = test_db()
        db.add(
            Input(
                run_id=sample_run,
                source_path="/path1",
                app="app1",
                scope="default",
                layer="app",
                stanza_type="monitor://",
            )
        )
        db.add(
            Input(
                run_id=sample_run,
                source_path="/path2",
                app="app2",
                scope="local",
                layer="app",
                stanza_type="tcp://",
            )
        )
        db.add(
            Input(
                run_id=sample_run,
                source_path="/path3",
                app="app1",
                scope="default",
                layer="system",
                stanza_type="monitor://",
            )
        )
        db.commit()
        db.close()

        # Filter by app
        response = client.get(f"/v1/runs/{sample_run}/inputs?app=app1")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

        # Filter by scope
        response = client.get(f"/v1/runs/{sample_run}/inputs?scope=local")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

        # Filter by stanza_type
        response = client.get(f"/v1/runs/{sample_run}/inputs?stanza_type=monitor://")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_list_inputs_run_not_found(self, client):
        """Test listing inputs for non-existent run returns 404."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        response = client.get("/v1/runs/99999/inputs")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


@pytest.mark.database
class TestPropsListEndpoint:
    """Tests for the GET /v1/runs/{id}/props endpoint."""

    def test_list_props_empty(self, client, sample_run):
        """Test listing props when there are none."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        response = client.get(f"/v1/runs/{sample_run}/props")

        assert response.status_code == 200
        data = response.json()

        assert data["props"] == []
        assert data["total"] == 0

    def test_list_props_with_data(self, client, test_db, sample_run):
        """Test listing props with actual data."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create test props
        db = test_db()
        for i in range(3):
            props = Props(
                run_id=sample_run,
                target=f"sourcetype_{i}",
                transforms_list=[f"transform_{i}"],
            )
            db.add(props)
        db.commit()
        db.close()

        response = client.get(f"/v1/runs/{sample_run}/props")

        assert response.status_code == 200
        data = response.json()

        assert len(data["props"]) == 3
        assert data["total"] == 3

    def test_list_props_filtering(self, client, test_db, sample_run):
        """Test filtering props by target."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create test props
        db = test_db()
        db.add(Props(run_id=sample_run, target="test_sourcetype"))
        db.add(Props(run_id=sample_run, target="other_sourcetype"))
        db.commit()
        db.close()

        # Filter by target
        response = client.get(f"/v1/runs/{sample_run}/props?target=test_sourcetype")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


@pytest.mark.database
class TestTransformsListEndpoint:
    """Tests for the GET /v1/runs/{id}/transforms endpoint."""

    def test_list_transforms_empty(self, client, sample_run):
        """Test listing transforms when there are none."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        response = client.get(f"/v1/runs/{sample_run}/transforms")

        assert response.status_code == 200
        data = response.json()

        assert data["transforms"] == []
        assert data["total"] == 0

    def test_list_transforms_with_data(self, client, test_db, sample_run):
        """Test listing transforms with actual data."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create test transforms
        db = test_db()
        for i in range(3):
            transform = Transform(
                run_id=sample_run,
                name=f"transform_{i}",
                dest_key="_MetaData:Index",
                regex=r".*",
            )
            db.add(transform)
        db.commit()
        db.close()

        response = client.get(f"/v1/runs/{sample_run}/transforms")

        assert response.status_code == 200
        data = response.json()

        assert len(data["transforms"]) == 3
        assert data["total"] == 3

    def test_list_transforms_filtering(self, client, test_db, sample_run):
        """Test filtering transforms by name."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create test transforms
        db = test_db()
        db.add(Transform(run_id=sample_run, name="test_transform"))
        db.add(Transform(run_id=sample_run, name="other_transform"))
        db.commit()
        db.close()

        # Filter by name
        response = client.get(f"/v1/runs/{sample_run}/transforms?name=test_transform")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


@pytest.mark.database
class TestIndexesListEndpoint:
    """Tests for the GET /v1/runs/{id}/indexes endpoint."""

    def test_list_indexes_empty(self, client, sample_run):
        """Test listing indexes when there are none."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        response = client.get(f"/v1/runs/{sample_run}/indexes")

        assert response.status_code == 200
        data = response.json()

        assert data["indexes"] == []
        assert data["total"] == 0

    def test_list_indexes_with_data(self, client, test_db, sample_run):
        """Test listing indexes with actual data."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create test indexes
        db = test_db()
        for i in range(3):
            index = Index(
                run_id=sample_run,
                name=f"index_{i}",
                kv={"homePath": f"/opt/splunk/var/lib/splunk/index_{i}/db"},
            )
            db.add(index)
        db.commit()
        db.close()

        response = client.get(f"/v1/runs/{sample_run}/indexes")

        assert response.status_code == 200
        data = response.json()

        assert len(data["indexes"]) == 3
        assert data["total"] == 3

    def test_list_indexes_filtering(self, client, test_db, sample_run):
        """Test filtering indexes by name."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create test indexes
        db = test_db()
        db.add(Index(run_id=sample_run, name="main"))
        db.add(Index(run_id=sample_run, name="test"))
        db.commit()
        db.close()

        # Filter by name
        response = client.get(f"/v1/runs/{sample_run}/indexes?name=main")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


@pytest.mark.database
class TestOutputsListEndpoint:
    """Tests for the GET /v1/runs/{id}/outputs endpoint."""

    def test_list_outputs_empty(self, client, sample_run):
        """Test listing outputs when there are none."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        response = client.get(f"/v1/runs/{sample_run}/outputs")

        assert response.status_code == 200
        data = response.json()

        assert data["outputs"] == []
        assert data["total"] == 0

    def test_list_outputs_with_data(self, client, test_db, sample_run):
        """Test listing outputs with actual data."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create test outputs
        db = test_db()
        for i in range(3):
            output = Output(
                run_id=sample_run,
                group_name=f"indexer_group_{i}",
                servers={"server": [f"indexer{i}.example.com:9997"]},
            )
            db.add(output)
        db.commit()
        db.close()

        response = client.get(f"/v1/runs/{sample_run}/outputs")

        assert response.status_code == 200
        data = response.json()

        assert len(data["outputs"]) == 3
        assert data["total"] == 3

    def test_list_outputs_filtering(self, client, test_db, sample_run):
        """Test filtering outputs by group_name."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create test outputs
        db = test_db()
        db.add(Output(run_id=sample_run, group_name="indexers"))
        db.add(Output(run_id=sample_run, group_name="forwarders"))
        db.commit()
        db.close()

        # Filter by group_name
        response = client.get(f"/v1/runs/{sample_run}/outputs?group_name=indexers")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


@pytest.mark.database
class TestServerclassesListEndpoint:
    """Tests for the GET /v1/runs/{id}/serverclasses endpoint."""

    def test_list_serverclasses_empty(self, client, sample_run):
        """Test listing serverclasses when there are none."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        response = client.get(f"/v1/runs/{sample_run}/serverclasses")

        assert response.status_code == 200
        data = response.json()

        assert data["serverclasses"] == []
        assert data["total"] == 0

    def test_list_serverclasses_with_data(self, client, test_db, sample_run):
        """Test listing serverclasses with actual data."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create test serverclasses
        db = test_db()
        for i in range(3):
            sc = Serverclass(
                run_id=sample_run,
                name=f"serverclass_{i}",
                whitelist={"0": f"host{i}*"},
                app="deployment-apps",
                scope="default",
                layer="app",
            )
            db.add(sc)
        db.commit()
        db.close()

        response = client.get(f"/v1/runs/{sample_run}/serverclasses")

        assert response.status_code == 200
        data = response.json()

        assert len(data["serverclasses"]) == 3
        assert data["total"] == 3

    def test_list_serverclasses_filtering(self, client, test_db, sample_run):
        """Test filtering serverclasses by various fields."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create test serverclasses
        db = test_db()
        db.add(
            Serverclass(
                run_id=sample_run,
                name="linux_hosts",
                app="app1",
                scope="default",
                layer="app",
            )
        )
        db.add(
            Serverclass(
                run_id=sample_run,
                name="windows_hosts",
                app="app2",
                scope="local",
                layer="app",
            )
        )
        db.commit()
        db.close()

        # Filter by name
        response = client.get(f"/v1/runs/{sample_run}/serverclasses?name=linux_hosts")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

        # Filter by app
        response = client.get(f"/v1/runs/{sample_run}/serverclasses?app=app2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


if __name__ == "__main__":
    print("✅ Typed listing endpoint tests configured")
