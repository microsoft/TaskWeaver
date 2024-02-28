import os
import signal
import time

from taskweaver.ces import Environment, EnvMode

env_id = os.getenv(
    "TASKWEAVER_ENV_ID",
    "local",
)
env_dir = os.getenv(
    "TASKWEAVER_ENV_DIR",
    "/app",
)
session_id = os.getenv(
    "TASKWEAVER_SESSION_ID",
    "session_id",
)
port_start = int(
    os.getenv(
        "TASKWEAVER_PORT_START",
        "12345",
    ),
)
kernel_id = os.getenv(
    "TASKWEAVER_KERNEL_ID",
    "kernel_id",
)

env = Environment(env_id, env_dir, env_mode=EnvMode.InsideContainer)


def signal_handler(sig, frame):
    print("Received termination signal. Shutting down the environment.")
    env.stop_session(session_id)
    exit(0)


# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    env.start_session(
        session_id=session_id,
        port_start_inside_container=port_start,
        kernel_id_inside_container=kernel_id,
    )

    print(f"Session {session_id} is running at {env_dir} inside a container.")

    # Keep the script running until it receives a termination signal
    try:
        # Keep the script running indefinitely
        while True:
            time.sleep(10)  # Sleep for 10 seconds
    except KeyboardInterrupt:
        # Handle Ctrl-C or other interruption signals
        pass
    finally:
        # Clean up and shut down the kernel
        env.stop_session(session_id)
