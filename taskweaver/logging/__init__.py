import logging
import os
from dataclasses import dataclass
from typing import Any, Dict

from injector import Module, provider

from taskweaver.config.module_config import ModuleConfig

# from .log_file import dump_log_file


class LoggingModuleConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("logging")

        import os

        app_dir = self.src.app_base_path

        self.remote = self._get_bool("remote", False)
        self.app_insights_connection_string = self._get_str(
            "appinsights_connection_string",
            None if self.remote else "",
        )
        self.injector = self._get_bool("injector", False)
        self.log_folder = self._get_str("log_folder", "logs")
        self.log_file = self._get_str("log_file", "task_weaver.log")
        self.log_full_path = os.path.join(app_dir, self.log_folder, self.log_file)


@dataclass
class TelemetryLogger:
    is_remote: bool
    logger: logging.Logger

    def telemetry_logging(
        self,
        telemetry_log_message: str,
        telemetry_log_content: Dict[str, Any],
    ):
        try:
            properties = {"custom_dimensions": telemetry_log_content}
            self.logger.warning(telemetry_log_message, extra=properties)
        except Exception as e:
            self.logger.error(f"Error in telemetry: {str(e)}")

    def dump_log_file(self, obj: Any, file_path: str):
        if isinstance(obj, (list, dict)):
            dumped_obj: Any = obj
        elif hasattr(obj, "to_dict"):
            dumped_obj = obj.to_dict()
        else:
            raise Exception(
                f"Object {obj} does not have to_dict method and also not a list or dict",
            )

        if not self.is_remote:
            import json

            with open(file_path, "w", encoding="utf-8") as log_file:
                json.dump(dumped_obj, log_file)
        else:
            self.telemetry_logging(
                telemetry_log_message=file_path,
                telemetry_log_content=dumped_obj,
            )

    def info(self, msg: str, *args: Any, **kwargs: Any):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any):
        self.logger.error(msg, *args, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any):
        self.logger.debug(msg, *args, **kwargs)


class LoggingModule(Module):
    @provider
    def provide_logger(self, config: LoggingModuleConfig) -> logging.Logger:
        logger = logging.getLogger(__name__)

        logger.setLevel(logging.INFO)

        if not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers):
            if not os.path.exists(config.log_full_path):
                os.makedirs(os.path.dirname(config.log_full_path), exist_ok=True)
                open(config.log_full_path, "w").close()
            file_handler = logging.FileHandler(config.log_full_path, encoding="utf-8")
            file_handler.setLevel(logging.INFO)
            log_format = "%(asctime)s - %(levelname)s - %(message)s"
            formatter = logging.Formatter(log_format)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        if config.injector:
            logging.getLogger("injector").setLevel(logging.INFO)

        return logger

    @provider
    def configure_remote_logging(
        self,
        config: LoggingModuleConfig,
        app_logger: logging.Logger,
    ) -> TelemetryLogger:
        if config.remote is not True:
            return TelemetryLogger(logger=app_logger, is_remote=False)
        telemetry_logger = logging.getLogger(__name__ + "_telemetry")

        from opencensus.ext.azure.log_exporter import AzureLogHandler  # type: ignore

        az_appinsights_connection_string = config.app_insights_connection_string
        assert (
            az_appinsights_connection_string is not None
        ), "az appinsights connection string must be set for remote logging mode"
        telemetry_logger = logging.getLogger(__name__ + "_telemetry")
        telemetry_logger.addHandler(
            AzureLogHandler(connection_string=az_appinsights_connection_string),
        )
        return TelemetryLogger(logger=telemetry_logger, is_remote=True)
