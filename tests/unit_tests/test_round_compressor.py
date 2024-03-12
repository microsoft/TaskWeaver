from injector import Injector

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.logging import LoggingModule
from taskweaver.memory import RoundCompressor


def test_round_compressor():
    from taskweaver.memory import Post, Round

    app_injector = Injector(
        [LoggingModule],
    )
    app_config = AppConfigSource(
        config={
            "llm.api_key": "test_key",
            "round_compressor.rounds_to_compress": 2,
            "round_compressor.rounds_to_retain": 2,
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    compressor = app_injector.get(RoundCompressor)

    assert compressor.rounds_to_compress == 2
    assert compressor.rounds_to_retain == 2

    round1 = Round.create(user_query="hello", id="round-1")
    post1 = Post.create(
        message="hello",
        send_from="User",
        send_to="Planner",
        attachment_list=[],
    )
    post2 = Post.create(
        message="hello",
        send_from="Planner",
        send_to="User",
        attachment_list=[],
    )
    round1.add_post(post1)
    round1.add_post(post2)

    summary, retained = compressor.compress_rounds(
        [round1],
        lambda x: x,
    )
    assert summary == "None"
    assert len(retained) == 1

    round2 = Round.create(user_query="hello", id="round-2")
    round2.add_post(post1)
    round2.add_post(post2)

    summary, retained = compressor.compress_rounds(
        [round1, round2],
        lambda x: x,
    )
    assert summary == "None"
    assert len(retained) == 2

    round3 = Round.create(user_query="hello", id="round-3")
    round3.add_post(post1)
    round3.add_post(post2)
    summary, retained = compressor.compress_rounds(
        [round1, round2, round3],
        lambda x: x,
    )
    assert summary == "None"
    assert len(retained) == 3

    round4 = Round.create(user_query="hello", id="round-4")
    round4.add_post(post1)
    round4.add_post(post2)
    summary, retained = compressor.compress_rounds(
        [round1, round2, round3, round4],
        lambda x: x,
    )
    assert summary == "None"
    assert len(retained) == 4
