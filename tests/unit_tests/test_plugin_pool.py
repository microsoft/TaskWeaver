import os

from injector import Injector

from taskweaver.code_interpreter.plugin_selection import SelectedPluginPool
from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.logging import LoggingModule
from taskweaver.memory.plugin import PluginModule, PluginRegistry


def test_plugin_pool():
    app_injector = Injector(
        [PluginModule, LoggingModule],
    )
    app_config = AppConfigSource(
        config={
            "app_dir": os.path.dirname(os.path.abspath(__file__)),
            "llm.api_key": "this_is_not_a_real_key",  # pragma: allowlist secret
            "plugin.base_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/plugins"),
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)

    plugin_registry = app_injector.get(PluginRegistry)

    plugins = plugin_registry.get_list()

    selected_plugin_pool = SelectedPluginPool()

    selected_plugin_pool.add_selected_plugins(plugins[:1])
    assert len(selected_plugin_pool) == 1

    selected_plugin_pool.add_selected_plugins(plugins[:1])
    assert len(selected_plugin_pool) == 1

    selected_plugin_pool.add_selected_plugins(plugins[1:3])
    assert len(selected_plugin_pool) == 3

    selected_plugin_pool.add_selected_plugins(plugins[2:4])
    assert len(selected_plugin_pool) == 4

    selected_plugin_pool.filter_unused_plugins("xcxcxc anomaly_detection() ababab")
    assert len(selected_plugin_pool) == 1
    assert selected_plugin_pool.get_plugins()[0].name == "anomaly_detection"

    selected_plugin_pool.filter_unused_plugins("")
    assert len(selected_plugin_pool) == 1

    selected_plugin_pool.add_selected_plugins(plugins[1:4])
    assert len(selected_plugin_pool) == 4

    selected_plugin_pool.filter_unused_plugins("abc sql_pull_data def")
    assert len(selected_plugin_pool) == 2

    selected_plugin_pool.filter_unused_plugins("")
    assert len(selected_plugin_pool) == 2
