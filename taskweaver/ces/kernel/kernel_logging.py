import logging
import os

logging.basicConfig(
    filename=os.environ.get("TASKWEAVER_LOGGING_FILE_PATH", "ces-runtime.log"),
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)
