from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from .context import LogErrorLevel, PluginContext


class Plugin(ABC):
    """
    base class for all plugins

    the instance of the plugin is a callable object, which is the entry point for
    the execution of the plugin function. The execution context and
    the configuration of the plugin are passed to the plugin instance when it is created.
    """

    def __init__(self, name: str, ctx: PluginContext, config: Dict[str, Any]) -> None:
        """
        create a plugin instance, this method will be called by the runtime

        :param name: the name of the plugin
        :param ctx: the execution context of the plugin
        :param config: the configuration of the plugin
        """
        super().__init__()
        self.name: str = name
        self.ctx: PluginContext = ctx
        self.config: Dict[str, Any] = config

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        entry point for the execution of the plugin function
        """

    def log(self, level: LogErrorLevel, message: str) -> None:
        """log a message from the plugin"""
        self.ctx.log(level, "Plugin-" + self.name, message)

    def get_env(self, variable_name: str) -> str:
        """get an environment variable from the context"""
        return self.ctx.get_env(self.name, variable_name)
