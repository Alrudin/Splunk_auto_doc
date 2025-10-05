#!/usr/bin/env python3
"""wait_for_db.py - Wait for PostgreSQL database to be ready.

This script ensures the database is ready before starting the application
or running migrations, preventing race conditions in local and CI environments.

Usage:
    python wait_for_db.py [--max-retries N] [--retry-interval N]
    
Environment variables:
    DATABASE_URL: Full database connection string (required)
    DB_MAX_RETRIES: Maximum number of retry attempts (default: 30)
    DB_RETRY_INTERVAL: Seconds between retries (default: 2)
"""

import os
import sys
import time
import argparse
from urllib.parse import urlparse

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def parse_database_url(url: str) -> dict[str, str]:
    """Parse DATABASE_URL into components."""
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "database": parsed.path.lstrip("/") if parsed.path else "postgres",
    }


def check_database_ready(db_params: dict[str, str]) -> bool:
    """Check if database is ready to accept connections.
    
    Args:
        db_params: Database connection parameters
        
    Returns:
        True if database is ready, False otherwise
    """
    try:
        from sqlalchemy import create_engine, text
        
        # Build connection URL
        url = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"
        
        # Create engine with short timeout
        engine = create_engine(
            url,
            echo=False,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 5}
        )
        
        # Try to connect and execute a simple query
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        engine.dispose()
        return True
        
    except Exception as e:
        # Print error for debugging but don't crash
        if "--verbose" in sys.argv:
            print(f"   Connection error: {e}", file=sys.stderr)
        return False


def wait_for_database(max_retries: int = 30, retry_interval: int = 2) -> bool:
    """Wait for database to become ready.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_interval: Seconds to wait between retries
        
    Returns:
        True if database became ready, False if timed out
    """
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set", file=sys.stderr)
        return False
    
    # Parse database URL
    try:
        db_params = parse_database_url(database_url)
    except Exception as e:
        print(f"❌ ERROR: Failed to parse DATABASE_URL: {e}", file=sys.stderr)
        return False
    
    print("🔍 Waiting for PostgreSQL database to be ready...")
    print(f"   Host: {db_params['host']}")
    print(f"   Port: {db_params['port']}")
    print(f"   Database: {db_params['database']}")
    print(f"   Max retries: {max_retries}")
    print(f"   Retry interval: {retry_interval}s")
    print("")
    
    # Retry loop
    for attempt in range(1, max_retries + 1):
        if check_database_ready(db_params):
            print(f"✅ PostgreSQL is ready! (attempt {attempt}/{max_retries})")
            return True
        
        print(f"⏳ Waiting for PostgreSQL... (attempt {attempt}/{max_retries})")
        
        if attempt < max_retries:
            time.sleep(retry_interval)
    
    # Timeout
    total_time = max_retries * retry_interval
    print("", file=sys.stderr)
    print(f"❌ ERROR: PostgreSQL did not become ready within {total_time} seconds", file=sys.stderr)
    print("", file=sys.stderr)
    print("Troubleshooting steps:", file=sys.stderr)
    print("  1. Check if PostgreSQL container is running: docker compose ps db", file=sys.stderr)
    print("  2. Check PostgreSQL logs: docker compose logs db", file=sys.stderr)
    print("  3. Verify DATABASE_URL environment variable is correct", file=sys.stderr)
    print("  4. Ensure PostgreSQL health check is configured in docker-compose.yml", file=sys.stderr)
    print("", file=sys.stderr)
    return False


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Wait for PostgreSQL database to be ready"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=int(os.getenv("DB_MAX_RETRIES", "30")),
        help="Maximum number of retry attempts (default: 30)"
    )
    parser.add_argument(
        "--retry-interval",
        type=int,
        default=int(os.getenv("DB_RETRY_INTERVAL", "2")),
        help="Seconds between retries (default: 2)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose error messages"
    )
    
    args = parser.parse_args()
    
    if wait_for_database(args.max_retries, args.retry_interval):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
