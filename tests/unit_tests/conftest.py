import os
from typing import Any, Dict, Optional, cast

import pytest


@pytest.fixture()
def app_injector(request: pytest.FixtureRequest):
    from injector import Injector

    from taskweaver.config.config_mgt import AppConfigSource
    from taskweaver.logging import LoggingModule
    from taskweaver.memory.plugin import PluginModule

    config: Dict[str, Any] = {}

    # default fixture provider
    config["llm.api_key"] = "test_key"
    config["plugin.base_path"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data/plugins",
    )

    # extra ones from marker
    extra_config_marker = cast(
        Optional[pytest.Mark],
        request.node.get_closest_marker("app_config"),
    )
    if extra_config_marker:
        extra_config = extra_config_marker.args[0]
        if type(extra_config) is dict:
            config.update(extra_config)
        else:
            raise Exception("app_config marker must be a dict")

    app_injector = Injector(
        [LoggingModule, PluginModule],
    )
    app_config = AppConfigSource(
        config=config,
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    return app_injector
