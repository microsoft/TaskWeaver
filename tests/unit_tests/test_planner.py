import os

from injector import Injector

from taskweaver.code_interpreter import CodeInterpreter
from taskweaver.code_interpreter.code_executor import CodeExecutor
from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.logging import LoggingModule
from taskweaver.memory import SharedMemoryEntry
from taskweaver.memory.attachment import AttachmentType
from taskweaver.memory.plugin import PluginModule
from taskweaver.module.event_emitter import SessionEventEmitter
from taskweaver.role.role import RoleModule, RoleRegistry
from taskweaver.session import SessionMetadata


class DummyManager:
    def __init__(self):
        pass

    def get_session_client(
        self,
        session_id,
        session_dir,
        cwd,
    ):
        return None

    def get_kernel_mode(self):
        return None


def test_compose_prompt():
    from taskweaver.memory import Attachment, Memory, Post, Round
    from taskweaver.planner import Planner

    app_injector = Injector(
        [LoggingModule, PluginModule, RoleModule],
    )
    app_config = AppConfigSource(
        config={
            "llm.api_key": "test_key",
            "plugin.base_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/plugins"),
            "planner.prompt_file_path": os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data/prompts/planner_prompt.yaml",
            ),
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    event_emitter = app_injector.get(SessionEventEmitter)
    app_injector.binder.bind(SessionEventEmitter, event_emitter)
    session_metadata = app_injector.create_object(
        SessionMetadata,
        {
            "session_id": "session_id",
            "workspace": "workspace",
            "execution_cwd": "execution_cwd",
        },
    )
    code_executor = app_injector.create_object(
        CodeExecutor,
        {
            "session_metadata": session_metadata,
            "exec_mgr": DummyManager(),
        },
    )
    app_injector.binder.bind(CodeExecutor, code_executor)
    role_reg = app_injector.get(RoleRegistry)
    role_entry = role_reg.get("code_interpreter")
    code_interpreter = app_injector.create_object(CodeInterpreter, {"role_entry": role_entry})
    planner = app_injector.create_object(
        Planner,
        {
            "workers": {code_interpreter.get_alias(): code_interpreter},
        },
    )

    post1 = Post.create(
        message="count the rows of /home/data.csv",
        send_from="User",
        send_to="Planner",
        attachment_list=[],
    )
    post2 = Post.create(
        message="Please load the data file /home/data.csv and count the rows of the loaded data",
        send_from="Planner",
        send_to="CodeInterpreter",
        attachment_list=[
            Attachment.create(
                AttachmentType.shared_memory_entry,
                content="add shared memory entry",
                extra=SharedMemoryEntry.create(
                    type="plan",
                    scope="round",
                    content=(
                        "1. load the data file\n2. count the rows of the loaded data <narrow depend on 1>\n"
                        "3. report the result to the user <wide depend on 2>"
                    ),
                ),
            ),
        ],
    )
    post2.add_attachment(
        Attachment.create(
            AttachmentType.init_plan,
            "1. load the data file\n2. count the rows of the loaded data <narrow depend on 1>\n"
            "3. report the result to the user <wide depend on 2>",
        ),
    )
    post2.add_attachment(
        Attachment.create(
            AttachmentType.plan,
            "1. instruct CodeInterpreter to load the data file and count the rows of the loaded data\n"
            "2. report the result to the user",
        ),
    )
    post2.add_attachment(
        Attachment.create(
            AttachmentType.current_plan_step,
            "1. instruct CodeInterpreter to load the data file and count the rows of the loaded data",
        ),
    )

    post3 = Post.create(
        message="Load the data file /home/data.csv successfully and there are 100 rows in the data file",
        send_from="CodeInterpreter",
        send_to="Planner",
        attachment_list=[],
    )

    post4 = Post.create(
        message="The data file /home/data.csv is loaded and there are 100 rows in the data file",
        send_from="Planner",
        send_to="User",
        attachment_list=[],
    )

    post4.add_attachment(
        Attachment.create(
            AttachmentType.init_plan,
            "1. load the data file\n2. count the rows of the loaded data <narrow depend on 1>\n3. report the result "
            "to the user <wide depend on 2>",
        ),
    )
    post4.add_attachment(
        Attachment.create(
            AttachmentType.plan,
            "1. instruct CodeInterpreter to load the data file and count the rows of the loaded data\n2. report the "
            "result to the user",
        ),
    )
    post4.add_attachment(Attachment.create(AttachmentType.current_plan_step, "2. report the result to the user"))

    round1 = Round.create(user_query="count the rows of ./data.csv", id="round-1")
    round1.add_post(post1)
    round1.add_post(post2)
    round1.add_post(post3)
    round1.add_post(post4)

    round2 = Round.create(user_query="hello", id="round-2")
    post5 = Post.create(
        message="hello",
        send_from="User",
        send_to="Planner",
        attachment_list=[],
    )
    round2.add_post(post5)

    memory = Memory(session_id="session-1")
    memory.conversation.add_round(round1)
    memory.conversation.add_round(round2)

    messages = planner.compose_prompt(rounds=memory.conversation.rounds)

    assert messages[0]["role"] == "system"
    assert messages[0]["content"].startswith(
        "You are the Planner who can coordinate Workers to finish the user task.",
    )
    assert "Arguments required: df: DataFrame, time_col_name: str, value_col_name: str" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == (
        "From: User\n" "Message: Let's start the new conversation!\n" "count the rows of /home/data.csv\n"
    )
    assert messages[2]["role"] == "assistant"
    assert messages[2]["content"] == (
        '{"response": {"init_plan": "1. load the data file\\n2. count the rows of the '
        "loaded data <narrow depend on 1>\\n3. report the result to the user <wide "
        'depend on 2>", "plan": "1. instruct CodeInterpreter to load the data file '
        'and count the rows of the loaded data\\n2. report the result to the user", '
        '"current_plan_step": "1. instruct CodeInterpreter to load the data file and '
        'count the rows of the loaded data", "send_to": "CodeInterpreter", "message": '
        '"Please load the data file /home/data.csv and count the rows of the loaded '
        'data"}}'
    )
    assert messages[3]["role"] == "user"
    assert messages[3]["content"] == (
        "From: CodeInterpreter\n"
        "Message: Load the data file /home/data.csv successfully and there are 100 "
        "rows in the data file\n"
    )
    assert messages[4]["role"] == "assistant"
    assert messages[4]["content"] == (
        '{"response": {"init_plan": "1. load the data file\\n2. count the rows of the '
        "loaded data <narrow depend on 1>\\n3. report the result to the user <wide "
        'depend on 2>", "plan": "1. instruct CodeInterpreter to load the data file '
        'and count the rows of the loaded data\\n2. report the result to the user", '
        '"current_plan_step": "2. report the result to the user", "send_to": "User", '
        '"message": "The data file /home/data.csv is loaded and there are 100 rows in '
        'the data file"}}'
    )
    assert messages[5]["role"] == "user"
    assert messages[5]["content"] == "From: User\nMessage: hello\n"


def test_compose_example_for_prompt():
    from taskweaver.memory import Memory, Post, Round
    from taskweaver.planner import Planner

    app_injector = Injector(
        [LoggingModule, PluginModule, RoleModule],
    )
    app_config = AppConfigSource(
        config={
            "llm.api_key": "test_key",
            "planner.use_example": True,
            "planner.example_base_path": os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data/examples/planner_examples",
            ),
            "plugin.base_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/plugins"),
            "planner.prompt_file_path": os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data/prompts/planner_prompt.yaml",
            ),
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    event_emitter = app_injector.get(SessionEventEmitter)
    app_injector.binder.bind(SessionEventEmitter, event_emitter)
    session_metadata = app_injector.create_object(
        SessionMetadata,
        {
            "session_id": "session_id",
            "workspace": "workspace",
            "execution_cwd": "execution_cwd",
        },
    )
    code_executor = app_injector.create_object(
        CodeExecutor,
        {
            "session_metadata": session_metadata,
            "exec_mgr": DummyManager(),
        },
    )
    app_injector.binder.bind(CodeExecutor, code_executor)
    role_reg = app_injector.get(RoleRegistry)
    role_entry = role_reg.get("code_interpreter")
    code_interpreter = app_injector.create_object(CodeInterpreter, {"role_entry": role_entry})
    planner = app_injector.create_object(
        Planner,
        {
            "workers": {code_interpreter.get_alias(): code_interpreter},
        },
    )

    round1 = Round.create(user_query="hello", id="round-1")
    post1 = Post.create(
        message="hello",
        send_from="User",
        send_to="Planner",
        attachment_list=[],
    )
    round1.add_post(post1)

    memory = Memory(session_id="session-1")
    memory.conversation.add_round(round1)

    messages = planner.compose_prompt(rounds=memory.conversation.rounds)

    assert messages[0]["role"] == "system"
    assert messages[0]["content"].startswith(
        "You are the Planner who can coordinate Workers to finish the user task.",
    )
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == (
        "From: User\n" "Message: Let's start the new conversation!\n" "count the rows of /home/data.csv\n"
    )
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "From: User\nMessage: Let's start the new conversation!\nhello\n"
