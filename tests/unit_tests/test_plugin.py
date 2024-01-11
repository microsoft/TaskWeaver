import os

from injector import Injector

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.logging import LoggingModule
from taskweaver.memory.plugin import PluginModule, PluginRegistry


def test_load_plugin_yaml():
    app_injector = Injector(
        [LoggingModule, PluginModule],
    )
    app_config = AppConfigSource(
        config={
            "plugin.base_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/plugins"),
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)

    plugin_registry = app_injector.get(PluginRegistry)

    assert len(plugin_registry.registry) == 4
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
        "# Examples:\n"
        '# df, description = anomaly_detection(df, time_col_name="ts", value_col_name="value")\n'
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

    assert plugin_registry.registry["klarna_search"].format_prompt() == (
        "# Search and compare prices from thousands of online shops. Only available in the US.\n"
        "# Examples:\n"
        '# df, description = klarna_search("phone")\n'
        '# df, description = klarna_search("phone", size=10)\n'
        '# df, description = klarna_search("phone", size=10, min_price=100, max_price=1000)\n'
        "def klarna_search(\n"
        "# A precise query that matches one very small category or product that needs "
        "to be searched for to find the products the user is looking for.  If the "
        "user explicitly stated what they want, use that as a query.  The query is as "
        "specific as possible to the product name or category mentioned by the user "
        "in its singular form, and don't contain any clarifiers like latest, newest, "
        "cheapest, budget, premium, expensive or similar.  The query is always taken "
        "from the latest topic, if there is a new topic a new query is started.  If "
        "the user speaks another language than English, translate their request into "
        "English (example: translate fia med knuff to ludo board game)!\n"
        "query: Any,\n"
        "# number of products to return\n"
        "size: Optional[int],\n"
        "# (Optional) Minimum price in local currency for the product searched for. "
        "Either explicitly stated by the user or implicitly inferred from a "
        "combination of the user's request and the kind of product searched for.\n"
        "min_price: Optional[int],\n"
        "# (Optional) Maximum price in local currency for the product searched for. "
        "Either explicitly stated by the user or implicitly inferred from a "
        "combination of the user's request and the kind of product searched for.\n"
        "max_price: Optional[int]) -> Tuple[\n"
        "# df: This DataFrame contains the search results.\n"
        "DataFrame,\n"
        "# description: This is a string describing the anomaly detection results.\n"
        "str]:...\n"
    )
