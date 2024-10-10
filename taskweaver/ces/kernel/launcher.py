import os
import sys

from taskweaver.ces.kernel.kernel_logging import logger

kernel_mode = os.getenv("TASKWEAVER_KERNEL_MODE", "local")
logger.info(f"Kernel mode: {kernel_mode}")


def configure_with_env(app):
    ces_dir = os.getenv(
        "TASKWEAVER_CES_DIR",
        os.path.join(os.path.dirname(__file__), "ces"),
    )

    cwd = os.getenv(
        "TASKWEAVER_CWD",
        os.path.dirname(__file__),
    )

    port_start = int(
        os.getenv(
            "TASKWEAVER_PORT_START",
            "12345",
        ),
    )

    ip = os.getenv(
        "TASKWEAVER_KERNEL_IP",
        "0.0.0.0",
    )

    session_id = os.getenv(
        "TASKWEAVER_SESSION_ID",
        "session_id",
    )

    kernel_id = os.getenv(
        "TASKWEAVER_KERNEL_ID",
        "kernel_id",
    )

    app.connection_file = os.path.join(ces_dir, f"conn-{session_id}-{kernel_id}.json")
    app.shell_port = port_start
    app.iopub_port = port_start + 1
    app.stdin_port = port_start + 2
    app.hb_port = port_start + 3
    app.control_port = port_start + 4
    app.ip = ip

    os.chdir(cwd)


def start_app():
    from ipykernel.kernelapp import IPKernelApp
    from ipykernel.zmqshell import ZMQInteractiveShell

    from taskweaver.ces.kernel.ext import TaskWeaverZMQShellDisplayHook

    # override displayhook_class for skipping output suppress token issue
    ZMQInteractiveShell.displayhook_class = TaskWeaverZMQShellDisplayHook

    app = IPKernelApp.instance()

    app.name = "taskweaver_kernel"
    app.config_file_name = os.path.join(
        os.path.dirname(__file__),
        "config.py",
    )
    app.extensions = ["taskweaver.ces.kernel.ctx_magic"]
    app.language = "python"

    # get config from env
    if kernel_mode == "container":
        configure_with_env(app)

    logger.info("Initializing app...")
    app.initialize()
    logger.info("Starting app...")
    app.start()


if __name__ == "__main__":
    if sys.path[0] == "":
        del sys.path[0]

    logger.info("Starting process...")
    logger.info("sys.path: %s", sys.path)
    logger.info("os.getcwd(): %s", os.getcwd())
    start_app()
