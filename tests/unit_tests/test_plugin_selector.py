import os

import pytest
from injector import Injector

from taskweaver.code_interpreter.code_generator.plugin_selection import PluginSelector
from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.memory.plugin import PluginModule

IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_plugin_selector():
    app_injector = Injector([PluginModule])
    app_config = AppConfigSource(
        config={
            "plugin.base_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/plugins"),
            "llm.embedding_api_type": "sentence_transformer",
            "llm.embedding_model": "all-mpnet-base-v2",
            "llm.api_key": "test_key",
            "code_generator.enable_auto_plugin_selection": True,
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    plugin_selector = app_injector.get(PluginSelector)
    plugin_selector.refresh()
    plugin_selector.load_plugin_embeddings()

    query1 = "detect abnormal data points in ./data.csv."
    selected_plugins = plugin_selector.plugin_select(query1, top_k=3)
    assert any([p.name == "anomaly_detection" for p in selected_plugins])
    assert len(selected_plugins) == 3
    assert selected_plugins[0].name == "anomaly_detection"

    query2 = "summarize ./paper.pdf."
    selected_plugins = plugin_selector.plugin_select(query2, top_k=3)

    assert any([p.name == "paper_summary" for p in selected_plugins])
