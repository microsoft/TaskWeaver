import os

from injector import Injector

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.logging import LoggingModule
from taskweaver.memory.attachment import AttachmentType
from taskweaver.memory.plugin import PluginModule


def test_compose_prompt():
    from taskweaver.memory import Attachment, Memory, Post, Round
    from taskweaver.planner import Planner

    app_injector = Injector(
        [LoggingModule, PluginModule],
    )
    app_config = AppConfigSource(
        config={
            "llm.api_key": "test_key",
            "plugin.base_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/plugins"),
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    planner = app_injector.create_object(Planner)

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
        attachment_list=[],
    )
    post2.add_attachment(
        Attachment.create(
            AttachmentType.init_plan,
            "1. load the data file\n2. count the rows of the loaded data <narrow depend on 1>\n3. report the result to the user <wide depend on 2>",
        ),
    )
    post2.add_attachment(
        Attachment.create(
            AttachmentType.plan,
            "1. instruct CodeInterpreter to load the data file and count the rows of the loaded data\n2. report the result to the user",
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
            "1. load the data file\n2. count the rows of the loaded data <narrow depend on 1>\n3. report the result to the user <wide depend on 2>",
        ),
    )
    post4.add_attachment(
        Attachment.create(
            AttachmentType.plan,
            "1. instruct CodeInterpreter to load the data file and count the rows of the loaded data\n2. report the result to the user",
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
        "You are the Planner who can coordinate CodeInterpreter to finish the user task.",
    )
    assert "Arguments required: df: DataFrame, time_col_name: str, value_col_name: str" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "User: Let's start the new conversation!\ncount the rows of /home/data.csv"
    assert messages[2]["role"] == "assistant"
    assert messages[2]["content"] == (
        '{"response": [{"type": "init_plan", "content": "1. load the data file\\n2. count the rows of the loaded data <narrow depend on 1>\\n3. report the result to the user <wide depend on 2>"}, {"type": "plan", "content": "1. instruct CodeInterpreter to load the data file and count the rows of the loaded data\\n2. report the result to the user"}, {"type": "current_plan_step", "content": "1. instruct CodeInterpreter to load the data file and count the rows of the loaded data"}, {"type": "send_to", "content": "CodeInterpreter"}, {"type": "message", "content": "Please load the data file /home/data.csv and count the rows of the loaded data"}]}'
    )
    assert messages[3]["role"] == "user"
    assert (
        messages[3]["content"]
        == "CodeInterpreter: Load the data file /home/data.csv successfully and there are 100 rows in the data file"
    )
    assert messages[4]["role"] == "assistant"
    assert (
        messages[4]["content"]
        == '{"response": [{"type": "init_plan", "content": "1. load the data file\\n2. count the rows of the loaded data <narrow depend on 1>\\n3. report the result to the user <wide depend on 2>"}, {"type": "plan", "content": "1. instruct CodeInterpreter to load the data file and count the rows of the loaded data\\n2. report the result to the user"}, {"type": "current_plan_step", "content": "2. report the result to the user"}, {"type": "send_to", "content": "User"}, {"type": "message", "content": "The data file /home/data.csv is loaded and there are 100 rows in the data file"}]}'
    )
    assert messages[5]["role"] == "user"
    assert messages[5]["content"] == "User: hello"


def test_compose_example_for_prompt():
    from taskweaver.memory import Memory, Post, Round
    from taskweaver.planner import Planner

    app_injector = Injector(
        [LoggingModule, PluginModule],
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
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    planner = app_injector.create_object(Planner)

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
        "You are the Planner who can coordinate CodeInterpreter to finish the user task.",
    )
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "User: Let's start the new conversation!\ncount the rows of /home/data.csv"
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "User: Let's start the new conversation!\nhello"


def test_skip_planning():
    from taskweaver.memory import Memory, Post, Round
    from taskweaver.planner import Planner

    app_injector = Injector(
        [LoggingModule, PluginModule],
    )
    app_config = AppConfigSource(
        config={
            "llm.api_key": "test_key",
            "plugin.base_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/plugins"),
            "planner.skip_planning": True,
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    planner = app_injector.create_object(Planner)
    planner.event_emitter.start_round("test_round")

    post1 = Post.create(
        message="count the rows of /home/data.csv",
        send_from="User",
        send_to="Planner",
        attachment_list=[],
    )

    round1 = Round.create(user_query="count the rows of ./data.csv", id="round-1")
    round1.add_post(post1)

    memory = Memory(session_id="session-1")
    memory.conversation.add_round(round1)

    response_post = planner.reply(
        memory,
        prompt_log_path=None,
        use_back_up_engine=False,
    )

    assert response_post.message == "Please process this request: count the rows of /home/data.csv"
    assert response_post.send_from == "Planner"
    assert response_post.send_to == "CodeInterpreter"
