import os
import sys

from taskweaver.ces.kernel.ext import TaskWeaverZMQShellDisplayHook
from taskweaver.ces.kernel.kernel_logging import logger

connection_file = os.getenv(
    "TASKWEAVER_CONNECTION_FILE",
    os.path.join(os.path.dirname(__file__), "taskweaver_connection_file.json"),
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


def start_app():
    from ipykernel.kernelapp import IPKernelApp
    from ipykernel.zmqshell import ZMQInteractiveShell

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
    app.connection_file = connection_file
    app.shell_port = port_start
    app.iopub_port = port_start + 1
    app.stdin_port = port_start + 2
    app.hb_port = port_start + 3
    app.control_port = port_start + 4
    app.ip = ip

    os.chdir(cwd)

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
