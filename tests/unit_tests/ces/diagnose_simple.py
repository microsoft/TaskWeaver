#!/usr/bin/env python
import sys

sys.path.insert(0, ".")

print("1. Starting", flush=True)

print("2. Importing code_execution_service_factory...", flush=True)
from taskweaver.ces import code_execution_service_factory

print("   Done", flush=True)

print("3. Creating temp dir...", flush=True)
import tempfile

tmp_dir = tempfile.mkdtemp(prefix="ces_diag_")
print(f"   {tmp_dir}", flush=True)

print("4. Creating manager...", flush=True)
manager = code_execution_service_factory(tmp_dir)
print(f"   Type: {type(manager).__name__}", flush=True)

print("5. Getting session client...", flush=True)
session = manager.get_session_client("diag-session")
print(f"   Type: {type(session).__name__}", flush=True)

print("6. Starting session (may hang here)...", flush=True)
session.start()
print("   Session started!", flush=True)

print("7. Executing code...", flush=True)
result = session.execute_code("test-1", "'hello'")
print(f"   Success: {result.is_success}, Output: {result.output}", flush=True)

print("8. Stopping...", flush=True)
session.stop()
manager.clean_up()
print("DONE", flush=True)
