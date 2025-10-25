"""Exception types for worker tasks."""


class WorkerError(Exception):
    """Base exception for worker errors."""

    pass


class PermanentError(WorkerError):
    """Permanent error that should not be retried.

    These errors indicate issues that won't be resolved by retrying,
    such as:
    - Malformed input data
    - Schema validation failures
    - Invalid archive format
    - Missing required data
    """

    pass


class TransientError(WorkerError):
    """Transient error that may succeed on retry.

    These errors indicate temporary issues that may resolve themselves,
    such as:
    - Network connectivity issues
    - Database connection errors
    - Temporary resource unavailability
    - Rate limiting
    """

    pass


class VisibilityTimeoutError(WorkerError):
    """Error raised when task exceeds visibility timeout without heartbeat."""

    pass
