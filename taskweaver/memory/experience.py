import json
import os
from dataclasses import dataclass
from typing import List, Literal, Optional, Tuple

import numpy as np
from injector import inject
from sklearn.metrics.pairwise import cosine_similarity

from taskweaver.config.module_config import ModuleConfig
from taskweaver.llm import LLMApi, format_chat_message
from taskweaver.logging import TelemetryLogger
from taskweaver.utils import read_yaml, write_yaml


@dataclass
class Experience:
    experience_text: str
    session_id: str
    embedding: Optional[List[float]] = None
    raw_experience_path: Optional[str] = None
    embedding_model: Optional[str] = None

    def to_dict(self):
        return {
            "experience_text": self.experience_text,
            "session_id": self.session_id,
            "embedding": self.embedding,
            "raw_experience_path": self.raw_experience_path,
            "embedding_model": self.embedding_model,
        }


class ExperienceConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("experience")

        self.session_history_dir = self._get_path(
            "session_history_dir",
            os.path.join(self.src.app_base_path, "experience"),
        )
        self.default_exp_prompt_path = self._get_path(
            "default_exp_prompt_path",
            os.path.join(
                os.path.dirname(__file__),
                "default_exp_prompt.yaml",
            ),
        )
        self.refresh_experience = self._get_bool("refresh_experience", False)
        self.retrieve_threshold = self._get_float("retrieve_threshold", 0.2)


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

        with open(self.config.default_exp_prompt_path, "r") as f:
            self.default_prompt_template = f.read()

        self.experience_list: List[Experience] = []

    @staticmethod
    def _preprocess_conversation_data(conv_data: dict, target_role: Literal["Planner", "CodeInterpreter"]):
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

        def select_role(conv_data, target_role):
            for round_data in conv_data:
                for idx, post in enumerate(round_data["post_list"]):
                    if post["send_from"] != target_role and post["send_to"] != target_role:
                        del round_data["post_list"][idx]

        conv_data = conv_data["rounds"]
        remove_id_fields(conv_data)
        select_role(conv_data, target_role)

        return conv_data

    def summarize_experience(
        self,
        session_id: str,
        prompt: Optional[str] = None,
        target_role: Literal["Planner", "CodeInterpreter"] = "Planner",
    ):
        raw_exp_file_path = os.path.join(self.config.session_history_dir, f"raw_exp_{session_id}.yaml")
        conversation = read_yaml(raw_exp_file_path)

        conversation = self._preprocess_conversation_data(conversation, target_role)

        system_instruction = prompt if prompt else self.default_prompt_template
        prompt = [
            format_chat_message("system", system_instruction),
            format_chat_message("user", json.dumps(conversation)),
        ]
        summarized_experience = self.llm_api.chat_completion(prompt)["content"]

        return summarized_experience

    def summarize_experience_in_batch(
        self,
        prompt: Optional[str] = None,
        target_role: Literal["Planner", "CodeInterpreter"] = "Planner",
    ):
        exp_files = os.listdir(self.config.session_history_dir)
        session_ids = [exp_file.split("_")[2].split(".")[0] for exp_file in exp_files if exp_file.startswith("raw_exp")]

        if len(session_ids) == 0:
            raise ValueError("No experience found.")

        for session_id in session_ids:
            exp_file_name = f"exp_{session_id}.yaml"
            # if the experience file already exists, load it
            if not self.config.refresh_experience and exp_file_name in os.listdir(self.config.session_history_dir):
                exp_file_path = os.path.join(self.config.session_history_dir, exp_file_name)
                experience = read_yaml(exp_file_path)
                experience_obj = Experience(**experience)
                self.experience_list.append(experience_obj)
                self.logger.info(f"Experience {exp_file_name} loaded.")
            else:
                # otherwise, summarize the experience and save it
                summarized_experience = self.summarize_experience(session_id, prompt, target_role)
                experience_obj = Experience(
                    experience_text=summarized_experience,
                    session_id=session_id,
                    raw_experience_path=os.path.join(
                        self.config.session_history_dir,
                        f"raw_exp_{session_id}.yaml",
                    ),
                )
                self.experience_list.append(experience_obj)
                self.logger.info("Experience created. Experience files number: {}".format(len(session_ids)))

        exp_embeddings = self.llm_api.get_embedding_list([exp.experience_text for exp in self.experience_list])
        for i, session_id in enumerate(session_ids):
            self.experience_list[i].embedding = exp_embeddings[i]
            self.experience_list[i].embedding_model = self.llm_api.config.embedding_model
        self.logger.info("Experience embeddings created. Embeddings number: {}".format(len(exp_embeddings)))

        for exp in self.experience_list:
            experience_file_path = os.path.join(self.config.session_history_dir, f"exp_{exp.session_id}.yaml")
            write_yaml(experience_file_path, exp.to_dict())
        self.logger.info("Experience obj saved.")

    def retrieve_experience(self, user_query: str) -> List[Tuple[Experience, float]]:
        user_query_embedding = np.array(self.llm_api.get_embedding(user_query))

        similarities = []

        for experience in self.experience_list:
            if experience.embedding_model != self.llm_api.config.embedding_model:
                raise ValueError(
                    "The embedding model of the experience is not the same as the current one."
                    "Please re-summarize the experience.",
                )

            similarity = cosine_similarity(
                user_query_embedding.reshape(
                    1,
                    -1,
                ),
                np.array(experience.embedding).reshape(1, -1),
            )
            similarities.append((experience, similarity))

        experience_rank = sorted(
            similarities,
            key=lambda x: x[1],
            reverse=True,
        )

        selected_experiences = [(exp, sim) for exp, sim in experience_rank if sim >= self.config.retrieve_threshold]

        return selected_experiences

    def delete_experience(self, session_id: str):
        exp_file_name = f"exp_{session_id}.yaml"
        if exp_file_name in os.listdir(self.config.session_history_dir):
            os.remove(os.path.join(self.config.session_history_dir, exp_file_name))
            os.remove(os.path.join(self.config.session_history_dir, f"raw_exp_{session_id}.yaml"))
            self.logger.info(f"Experience {exp_file_name} deleted.")
        else:
            self.logger.info(f"Experience {exp_file_name} not found.")
