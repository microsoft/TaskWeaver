"""Code Execution Service Manager package.

This package provides manager implementations for code execution:
- ExecutionServiceProvider: HTTP server-based execution (default)
- DeferredManager: Lazy initialization wrapper
- SubProcessManager: Used internally by the server for kernel management
"""

from taskweaver.ces.manager.defer import DeferredClient, DeferredManager
from taskweaver.ces.manager.execution_service import ExecutionServiceClient, ExecutionServiceProvider
from taskweaver.ces.manager.sub_proc import SubProcessClient, SubProcessManager

__all__ = [
    # Internal (used by server)
    "SubProcessManager",
    "SubProcessClient",
    # Server mode (default)
    "ExecutionServiceProvider",
    "ExecutionServiceClient",
    # Deferred wrappers
    "DeferredManager",
    "DeferredClient",
]
