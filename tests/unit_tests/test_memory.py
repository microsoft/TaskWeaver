def test_memory_get_rounds():
    from taskweaver.memory import Memory, Post, Round
    from taskweaver.module.prompt_util import PromptUtil

    post1 = Post.create(
        message="create a dataframe",
        send_from="Planner",
        send_to="CodeInterpreter",
        attachment_list=[],
    )
    post2 = Post.create(
        message="A dataframe `df` with 10 rows and 2 columns: "
        + PromptUtil.wrap_text_with_delimiter(
            "'DATE' and 'VALUE' has been generated.",
            PromptUtil.DELIMITER_TEMPORAL,
        ),
        send_from="CodeInterpreter",
        send_to="Planner",
        attachment_list=[],
    )

    round1 = Round.create(user_query="hello", id="round-1")
    round1.add_post(post1)
    round1.add_post(post2)

    round2 = Round.create(user_query="hello again", id="round-2")
    post3 = Post.create(
        message="what is the data range",
        send_from="Planner",
        send_to="CodeInterpreter",
        attachment_list=[],
    )
    post4 = Post.create(
        message="The data range for the 'VALUE' column is "
        + PromptUtil.wrap_text_with_delimiter("0.94", PromptUtil.DELIMITER_TEMPORAL),
        send_from="CodeInterpreter",
        send_to="Planner",
        attachment_list=[],
    )

    round2.add_post(post3)
    round2.add_post(post4)

    round3 = Round.create(user_query="hello again", id="round-3")
    post5 = Post.create(
        message="what is the max value?",
        send_from="Planner",
        send_to="CodeInterpreter",
        attachment_list=[],
    )
    post6 = Post.create(
        message="The max value is " + PromptUtil.wrap_text_with_delimiter("0.94", PromptUtil.DELIMITER_TEMPORAL),
        send_from="CodeInterpreter",
        send_to="Planner",
        attachment_list=[],
    )
    round3.add_post(post5)
    round3.add_post(post6)

    memory = Memory(session_id="session-1")
    memory.conversation.add_round(round1)
    memory.conversation.add_round(round2)
    memory.conversation.add_round(round3)

    rounds = memory.get_role_rounds(role="Planner")
    assert len(rounds) == 3
    assert rounds[0].post_list[0].message == "create a dataframe"
    assert rounds[0].post_list[1].message == "A dataframe `df` with 10 rows and 2 columns: "
    assert rounds[1].post_list[0].message == "what is the data range"
    assert rounds[1].post_list[1].message == "The data range for the 'VALUE' column is "
    assert rounds[2].post_list[0].message == "what is the max value?"
    assert rounds[2].post_list[1].message == "The max value is 0.94"

    # the rounds are deeply copied, so the original memory should not be changed
    rounds[0].post_list[0].message = "create a dataframe 1"
    assert rounds[0].post_list[0].message == "create a dataframe 1"
    assert memory.conversation.rounds[0].post_list[0].message == "create a dataframe"
