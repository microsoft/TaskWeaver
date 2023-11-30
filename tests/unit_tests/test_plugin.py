import os

from injector import Injector

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.logging import LoggingModule
from taskweaver.memory.plugin import PluginModule, PluginRegistry


def test_load_plugin_yaml():
    app_injector = Injector(
        [PluginModule, LoggingModule],
    )
    app_config = AppConfigSource(
        config={
            "plugin.base_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/plugins"),
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)

    plugin_registry = app_injector.get(PluginRegistry)

    assert len(plugin_registry.registry) == 2
    assert "anomaly_detection" in plugin_registry.registry
    assert plugin_registry.registry["anomaly_detection"].spec.name == "anomaly_detection"
    assert plugin_registry.registry["anomaly_detection"].spec.description.startswith(
        "anomaly_detection function identifies anomalies",
    )
    assert plugin_registry.registry["anomaly_detection"].impl == "anomaly_detection"
    assert len(plugin_registry.registry["anomaly_detection"].spec.args) == 3
    assert plugin_registry.registry["anomaly_detection"].spec.args[0].name == "df"
    assert plugin_registry.registry["anomaly_detection"].spec.args[0].type == "DataFrame"
    assert (
        plugin_registry.registry["anomaly_detection"].spec.args[0].description
        == "the input data from which we can identify the "
        "anomalies with the 3-sigma algorithm."
    )
    assert plugin_registry.registry["anomaly_detection"].spec.args[0].required == True

    assert len(plugin_registry.registry["anomaly_detection"].spec.returns) == 2
    assert plugin_registry.registry["anomaly_detection"].spec.returns[0].name == "df"
    assert plugin_registry.registry["anomaly_detection"].spec.returns[0].type == "DataFrame"
    assert (
        plugin_registry.registry["anomaly_detection"].spec.returns[0].description == "This DataFrame extends the input "
        "DataFrame with a newly-added column "
        '"Is_Anomaly" containing the anomaly detection result.'
    )


def test_plugin_format_prompt():
    app_injector = Injector(
        [PluginModule, LoggingModule],
    )
    app_config = AppConfigSource(
        config={
            "plugin.base_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/plugins"),
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)

    plugin_registry = app_injector.get(PluginRegistry)

    assert plugin_registry.registry["anomaly_detection"].format_prompt() == (
        "# anomaly_detection function identifies anomalies from an input DataFrame of time series. It will add a new "
        'column "Is_Anomaly", where each entry will be marked with "True" if the value is an anomaly or "False" '
        "otherwise.\n"
        "def anomaly_detection(\n"
        "# the input data from which we can identify the anomalies with the 3-sigma algorithm.\n"
        "df: Any,\n"
        "# name of the column that contains the datetime\n"
        "time_col_name: Any,\n"
        "# name of the column that contains the numeric values.\n"
        "value_col_name: Any) -> Tuple[\n"
        '# df: This DataFrame extends the input DataFrame with a newly-added column "Is_Anomaly" containing the '
        "anomaly detection result.\n"
        "DataFrame,\n"
        "# description: This is a string describing the anomaly detection results.\n"
        "str]:...\n"
    )
