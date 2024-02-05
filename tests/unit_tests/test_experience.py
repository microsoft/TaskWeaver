import os

import pytest
from injector import Injector

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.logging import LoggingModule
from taskweaver.memory.experience import ExperienceGenerator

IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_experience_retrieval():
    app_injector = Injector([LoggingModule])
    app_config = AppConfigSource(
        config_file_path=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "..",
            "project/taskweaver_config.json",
        ),
        config={
            "llm.embedding_api_type": "sentence_transformers",
            "llm.embedding_model": "all-mpnet-base-v2",
            "experience.experience_dir": os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data/experience",
            ),
            "experience.refresh_experience": False,
            "experience.retrieve_threshold": 0.0,
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    experience_manager = app_injector.create_object(ExperienceGenerator)

    user_query = "show top 10 data in ./data.csv"

    experience_manager.refresh(target_role="Planner")
    experience_manager.load_experience(target_role="Planner")

    assert len(experience_manager.experience_list) == 1
    exp = experience_manager.experience_list[0]
    assert len(exp.experience_text) > 0
    assert exp.exp_id == "test-exp-1"
    assert len(exp.embedding) == 768
    assert exp.embedding_model == "all-mpnet-base-v2"

    experiences = experience_manager.retrieve_experience(user_query=user_query)

    assert len(experiences) == 1
    assert experiences[0][0].exp_id == "test-exp-1"
