from taskweaver.memory.plugin import PluginEntry, PluginParameter, PluginSpec


def test_function_formatting():
    plugin = PluginEntry(
        name="test",
        impl="test",
        spec=PluginSpec(
            name="test",
            description="test",
            args=[
                PluginParameter(
                    name="arg1",
                    type="string",
                    description="arg1",
                    required=True,
                ),
                PluginParameter(
                    name="arg2",
                    type="integer",
                    description="arg2",
                    required=False,
                ),
                PluginParameter(
                    name="arg3",
                    type="float",
                    description="arg3",
                    required=False,
                ),
                PluginParameter(
                    name="arg4",
                    type="boolean",
                    description="arg4",
                    required=False,
                ),
                PluginParameter(
                    name="arg5",
                    type="none",
                    description="arg5",
                    required=False,
                ),
            ],
        ),
        config={"test_key": "test_val"},
        required=False,
        enabled=True,
        plugin_only=True,
    )
    assert plugin.format_function_calling() == {
        "type": "function",
        "function": {
            "name": "test",
            "description": "test",
            "parameters": {
                "type": "object",
                "properties": {
                    "arg1": {"type": "string", "description": "arg1"},
                    "arg2": {"type": "integer", "description": "arg2"},
                    "arg3": {"type": "number", "description": "arg3"},
                    "arg4": {"type": "boolean", "description": "arg4"},
                    "arg5": {"type": "null", "description": "arg5"},
                },
                "required": ["arg1"],
            },
        },
    }
