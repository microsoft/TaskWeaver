import json
import os
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
from injector import inject
from sklearn.metrics.pairwise import cosine_similarity

from taskweaver.config.module_config import ModuleConfig
from taskweaver.llm import LLMApi, format_chat_message
from taskweaver.logging import TelemetryLogger


@dataclass
class Experience:
    experience_text: str
    session_id: str
    embedding: Optional[List[float]] = None
    raw_experience_path: Optional[str] = None


class ExperienceConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("experience")

        self.session_history_dir = self._get_path(
            "session_history_dir",
            os.path.join(self.src.app_base_path, "experience"),
        )
        self.default_exp_prompt_template_path = self._get_path(
            "default_exp_prompt_template_path",
            os.path.join(
                os.path.dirname(__file__),
                "default_exp_prompt_template.yaml",
            ),
        )


class ExperienceManger:
    @inject
    def __init__(
        self,
        llm_api: LLMApi,
        config: ExperienceConfig,
        logger: TelemetryLogger,
    ):
        self.config = config
        self.llm_api = llm_api
        self.logger = logger

        with open(self.config.default_exp_prompt_template_path, "r") as f:
            self.default_prompt_template = f.read()

        self.experience_list: List[Experience] = []

    @staticmethod
    def _preprocess_session_data(session_data: dict) -> dict:
        def remove_id_fields(d):
            if isinstance(d, dict):
                for key in list(d.keys()):
                    if key == "id":
                        del d[key]
                    else:
                        remove_id_fields(d[key])
            elif isinstance(d, list):
                for item in d:
                    remove_id_fields(item)

        session_data = session_data["rounds"]
        remove_id_fields(session_data)

        return session_data

    def summarize_experience(
        self,
        session_id: str,
        prompt_template: Optional[str] = None,
    ):
        with open(os.path.join(self.config.session_history_dir, f"exp_{session_id}.json"), "r") as f:
            session_data = json.load(f)
        session_data = self._preprocess_session_data(session_data)

        if prompt_template is None:
            system_instruction = self.default_prompt_template
        prompt = [
            format_chat_message("system", system_instruction),
            format_chat_message("user", json.dumps(session_data)),
        ]
        summarized_experience = self.llm_api.chat_completion(prompt)["content"]

        return summarized_experience

    def summarize_experience_in_batch(self):
        session_ids = os.listdir(self.config.session_history_dir)

        if len(session_ids) == 0:
            self.logger.info("No experience file found.")
            return

        for session_id in session_ids:
            exp_file_name = f"summarized_exp_{session_id}.json"
            if exp_file_name in os.listdir(self.config.session_history_dir):
                continue
            summarized_experience = self.summarize_experience(session_id)
            with open(os.path.join(self.config.session_history_dir, exp_file_name, "w")) as f:
                json.dump({"experience": summarized_experience, "session_id": session_id}, f)
            self.experience_list.append(
                Experience(
                    experience_text=summarized_experience,
                    session_id=session_id,
                    raw_experience_path=os.path.join(
                        self.config.session_history_dir,
                        f"raw_exp_{session_id}.json",
                    ),
                ),
            )
        self.logger.info("Summarized experience created. Experience files number: {}".format(len(session_ids)))

        exp_embeddings = self.llm_api.get_embedding_list([exp.experience_text for exp in self.experience_list])
        for i, session_id in enumerate(session_ids):
            self.experience_list[i].embedding = exp_embeddings[i]
        self.logger.info("Summarized experience embeddings created. Embeddings number: {}".format(len(exp_embeddings)))

    def retrieve_experience(self, user_query: str, threshold: float = 0.5):
        user_query_embedding = np.array(self.llm_api.get_embedding(user_query))

        similarities = []

        for experience in self.experience_list:
            similarity = cosine_similarity(
                user_query_embedding.reshape(
                    1,
                    -1,
                ),
                np.array(experience.embedding).reshape(1, -1),
            )
            similarities.append((experience.session_id, experience.experience_text, similarity))

        experience_rank = sorted(
            similarities,
            key=lambda x: x[2],
            reverse=True,
        )

        selected_experiences = [exp for sid, exp, sim in experience_rank if sim >= threshold]

        return selected_experiences
