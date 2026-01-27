import sys
import time

from taskweaver.plugin import Plugin, register_plugin


@register_plugin
class LongRunningDemo(Plugin):
    """
    A demo plugin that simulates a long-running task with progress updates.
    This demonstrates real-time streaming of print() output during execution.
    """

    def __call__(self, steps: int = 5, delay: float = 1.0) -> str:
        print(f"Starting long-running task with {steps} steps...")
        sys.stdout.flush()

        for i in range(1, steps + 1):
            time.sleep(delay)
            print(f"Progress: {i}/{steps} - Processing step {i}")
            sys.stdout.flush()

        print("Task completed successfully!")
        sys.stdout.flush()

        return f"Completed {steps} steps in {steps * delay:.1f} seconds"
