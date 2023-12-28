import os

import pytest
import yaml
from injector import Injector
from tests.unit_tests.test_embedding import IN_GITHUB_ACTIONS

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.logging import LoggingModule
from taskweaver.memory.experience import ExperienceManger


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_experience_generation():
    app_injector = Injector([LoggingModule])
    app_config = AppConfigSource(
        config={
            # need to configure llm related config to run this test
            # please refer to the https://microsoft.github.io/TaskWeaver/docs/llms
            "llm.embedding_api_type": "sentence_transformer",
            "llm.embedding_model": "all-mpnet-base-v2",
            "experience.session_history_dir": os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data/experience",
            ),
            "experience.refresh_experience": True,
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    experience_manager = app_injector.create_object(ExperienceManger)

    experience_manager.summarize_experience_in_batch()

    exp_files = os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/experience"))
    assert len(exp_files) == 2
    assert "exp_test-session-1.yaml" in exp_files

    assert len(experience_manager.experience_list) == 1
    exp = experience_manager.experience_list[0]
    assert len(exp.experience_text) > 0
    assert exp.session_id == "test-session-1"
    assert len(exp.embedding) == 768
    assert exp.raw_experience_path == os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "experience",
        "raw_exp_test-session-1.yaml",
    )
    assert exp.embedding_model == "all-mpnet-base-v2"

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/experience/exp_test-session-1.yaml")) as f:
        exp = yaml.safe_load(f)
    assert "experience_text" in exp
    assert exp["session_id"] == "test-session-1"
    assert len(exp["embedding"]) == 768
    assert exp["raw_experience_path"] == os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "experience",
        "raw_exp_test-session-1.yaml",
    )
    assert exp["embedding_model"] == "all-mpnet-base-v2"


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_experience_retrieval():
    app_injector = Injector([LoggingModule])
    app_config = AppConfigSource(
        config={
            "llm.embedding_api_type": "sentence_transformer",
            "llm.embedding_model": "all-mpnet-base-v2",
            "experience.session_history_dir": os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data/experience",
            ),
            "experience.refresh_experience": False,
            "experience.retrieve_threshold": 0.0,
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    experience_manager = app_injector.create_object(ExperienceManger)

    user_query = "show top 10 data in ./data.csv"

    experience_manager.summarize_experience_in_batch()

    assert len(experience_manager.experience_list) == 1
    exp = experience_manager.experience_list[0]
    assert len(exp.experience_text) > 0
    assert exp.session_id == "test-session-1"
    assert len(exp.embedding) == 768
    assert exp.raw_experience_path == os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "experience",
        "raw_exp_test-session-1.yaml",
    )
    assert exp.embedding_model == "all-mpnet-base-v2"

    experiences = experience_manager.retrieve_experience(user_query=user_query)

    assert len(experiences) == 1
    assert experiences[0][1] > experience_manager.config.retrieve_threshold
    print("similarity: ", experiences[0][1])
    assert experiences[0][0].session_id == "test-session-1"
