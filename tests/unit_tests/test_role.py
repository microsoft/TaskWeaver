import os

import pytest
from injector import Injector

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.logging import LoggingModule
from taskweaver.memory import Attachment, Memory, Post, Round, SharedMemoryEntry
from taskweaver.memory.attachment import AttachmentType
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

    role.role_load_experience("test")
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

    memory = Memory(session_id="session-1")

    role.role_load_experience("test", memory=memory)
    assert len(role.experience_generator.experience_list) == 0

    post1 = Post.create(
        message="create a dataframe",
        send_from="Planner",
        send_to="CodeInterpreter",
        attachment_list=[
            Attachment.create(
                type=AttachmentType.shared_memory_entry,
                content="",
                extra=SharedMemoryEntry.create(
                    type="experience_sub_path",
                    content="sub_path",
                    scope="conversation",
                ),
            ),
        ],
    )
    round1 = Round.create(user_query="hello", id="round-1")
    round1.add_post(post1)
    memory.conversation.add_round(round1)

    role.role_load_experience("test", memory=memory)
    assert len(role.experience_generator.experience_list) == 1

    try:
        role.role_load_experience("test")
    except AssertionError as e:
        assert str(e) == "Memory should be provided when dynamic_experience_sub_path is True"
