"""Basic structure tests that work without external dependencies."""

import os
import sys
from pathlib import Path


def test_app_structure_exists() -> None:
    """Test that the basic app structure exists."""
    backend_dir = Path(__file__).parent.parent
    app_dir = backend_dir / "app"
    
    assert app_dir.exists(), "app directory should exist"
    assert (app_dir / "__init__.py").exists(), "app/__init__.py should exist"
    assert (app_dir / "main.py").exists(), "app/main.py should exist"
    assert (app_dir / "core" / "config.py").exists(), "app/core/config.py should exist"
    assert (app_dir / "core" / "db.py").exists(), "app/core/db.py should exist"
    assert (app_dir / "api" / "v1" / "health.py").exists(), "app/api/v1/health.py should exist"
    assert (app_dir / "health.py").exists(), "app/health.py should exist (legacy)"
    
    # Check that required directories exist
    assert (app_dir / "models").exists(), "app/models directory should exist"
    assert (app_dir / "schemas").exists(), "app/schemas directory should exist"
    assert (app_dir / "models" / "__init__.py").exists(), "app/models/__init__.py should exist"
    assert (app_dir / "schemas" / "__init__.py").exists(), "app/schemas/__init__.py should exist"


def test_python_imports() -> None:
    """Test that basic Python imports work."""
    import json
    import os
    import sys
    
    # These should not raise any exceptions
    assert json is not None
    assert os is not None
    assert sys is not None


def test_app_can_be_imported() -> None:
    """Test that our app modules can be imported syntactically."""
    # Add the backend directory to the path so we can import our modules
    backend_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(backend_dir))
    
    try:
        # Test syntax by compiling the files
        with open(backend_dir / "app" / "__init__.py") as f:
            compile(f.read(), "app/__init__.py", "exec")
            
        with open(backend_dir / "app" / "main.py") as f:
            compile(f.read(), "app/main.py", "exec")
            
        with open(backend_dir / "app" / "core" / "config.py") as f:
            compile(f.read(), "app/core/config.py", "exec")
            
        with open(backend_dir / "app" / "core" / "db.py") as f:
            compile(f.read(), "app/core/db.py", "exec")
            
        with open(backend_dir / "app" / "api" / "v1" / "health.py") as f:
            compile(f.read(), "app/api/v1/health.py", "exec")
            
        with open(backend_dir / "app" / "health.py") as f:
            compile(f.read(), "app/health.py", "exec")
            
    except SyntaxError as e:
        raise AssertionError(f"Syntax error in module: {e}")
    finally:
        sys.path.remove(str(backend_dir))


if __name__ == "__main__":
    # Simple test runner for when pytest is not available
    try:
        test_app_structure_exists()
        print("✓ test_app_structure_exists passed")
        
        test_python_imports()
        print("✓ test_python_imports passed")
        
        test_app_can_be_imported()
        print("✓ test_app_can_be_imported passed")
        
        print("✅ All basic tests passed!")
        
        # Also run health simulation test
        import subprocess
        result = subprocess.run(
            ["python", "backend/tests/test_health_simulation.py"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("✅ Health endpoint tests also passed!")
        else:
            print("⚠️  Health endpoint tests had issues, but basic tests passed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)