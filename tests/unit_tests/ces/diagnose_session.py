#!/usr/bin/env python
"""Diagnostic script to identify where test_session.py hangs.

Run with: conda run -n taskweaver python tests/unit_tests/ces/diagnose_session.py
"""

import sys
import time


def timestamp():
    return f"[{time.strftime('%H:%M:%S')}]"


def log(msg: str):
    print(f"{timestamp()} {msg}", flush=True)


def main():
    log("=== Starting CES Session Diagnostics ===")

    # Step 1: Import test
    log("Step 1: Testing imports...")
    start = time.time()
    try:
        from taskweaver.ces import code_execution_service_factory

        log(f"  Imports OK ({time.time() - start:.2f}s)")
    except Exception as e:
        log(f"  FAILED: {e}")
        return 1

    # Step 2: Create manager (should be fast - deferred)
    log("Step 2: Creating manager (deferred)...")
    start = time.time()
    try:
        import tempfile

        tmp_dir = tempfile.mkdtemp(prefix="ces_diag_")
        manager = code_execution_service_factory(tmp_dir)
        log(f"  Manager created ({time.time() - start:.2f}s)")
        log(f"  Type: {type(manager).__name__}")
    except Exception as e:
        log(f"  FAILED: {e}")
        return 1

    # Step 3: Get session client (should be fast - deferred)
    log("Step 3: Getting session client (deferred)...")
    start = time.time()
    try:
        session = manager.get_session_client("diag-session")
        log(f"  Session client created ({time.time() - start:.2f}s)")
        log(f"  Type: {type(session).__name__}")
    except Exception as e:
        log(f"  FAILED: {e}")
        return 1

    # Step 4: Start session (THIS triggers actual initialization)
    log("Step 4: Starting session (triggers server + kernel init)...")
    log("  This is where the hang likely occurs...")
    start = time.time()
    try:
        session.start()
        log(f"  Session started ({time.time() - start:.2f}s)")
    except Exception as e:
        log(f"  FAILED after {time.time() - start:.2f}s: {e}")
        import traceback

        traceback.print_exc()
        return 1

    # Step 5: Execute simple code
    log("Step 5: Executing simple code...")
    start = time.time()
    try:
        result = session.execute_code("test-1", "'hello'")
        log(f"  Execution completed ({time.time() - start:.2f}s)")
        log(f"  Success: {result.is_success}")
        log(f"  Output: {result.output}")
        if result.error:
            log(f"  Error: {result.error}")
    except Exception as e:
        log(f"  FAILED after {time.time() - start:.2f}s: {e}")
        import traceback

        traceback.print_exc()
        return 1

    # Step 6: Stop session
    log("Step 6: Stopping session...")
    start = time.time()
    try:
        session.stop()
        log(f"  Session stopped ({time.time() - start:.2f}s)")
    except Exception as e:
        log(f"  FAILED: {e}")
        return 1

    # Step 7: Cleanup manager
    log("Step 7: Cleaning up manager...")
    start = time.time()
    try:
        manager.clean_up()
        log(f"  Manager cleaned up ({time.time() - start:.2f}s)")
    except Exception as e:
        log(f"  FAILED: {e}")
        return 1

    log("=== All steps completed successfully ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
