import os
import sys

from .logging import logger


def start_app():
    from ipykernel.kernelapp import IPKernelApp

    app = IPKernelApp.instance()
    app.config_file_name = os.path.join(
        os.path.dirname(__file__),
        "config.py",
    )
    app.extensions = ["taskweaver.ces.kernel.ctx_magic"]

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
