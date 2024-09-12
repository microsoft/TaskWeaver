import os

import pytest
from injector import Injector

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.logging import LoggingModule
from taskweaver.memory.experience import ExperienceGenerator
from taskweaver.memory.plugin import PluginModule
from taskweaver.role import Role

IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_role_load_experience():
    app_injector = Injector(
        [PluginModule, LoggingModule],
    )
    app_config = AppConfigSource(
        config={
            "app_dir": os.path.dirname(os.path.abspath(__file__)),
            "llm.api_key": "this_is_not_a_real_key",  # pragma: allowlist secret
            "role.use_experience": True,
            "role.experience_dir": os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data/experience",
            ),
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)

    role = app_injector.create_object(Role, {"role_entry": None})

    role.experience_generator = app_injector.create_object(ExperienceGenerator)

    role.load_experience("test")
    assert len(role.experience_generator.experience_list) == 1


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_role_load_experience_sub_path():
    app_injector = Injector(
        [PluginModule, LoggingModule],
    )
    app_config = AppConfigSource(
        config={
            "app_dir": os.path.dirname(os.path.abspath(__file__)),
            "llm.api_key": "this_is_not_a_real_key",  # pragma: allowlist secret
            "role.use_experience": True,
            "role.experience_dir": os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data/experience",
            ),
            "role.dynamic_experience_sub_path": True,
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)

    role = app_injector.create_object(Role, {"role_entry": None})

    role.experience_generator = app_injector.create_object(ExperienceGenerator)

    role.load_experience("test")
    assert len(role.experience_generator.experience_list) == 0

    role.load_experience("test", "sub_path")
    assert len(role.experience_generator.experience_list) == 1

    try:
        role.load_experience("test")
    except AssertionError as e:
        assert str(e) == "sub_path is empty when dynamic_experience_sub_path is True"
