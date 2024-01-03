import json
import os
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

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
    raw_experience_path: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding: List[float] = field(default_factory=list)

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "experience_text": self.experience_text,
            "raw_experience_path": self.raw_experience_path,
            "embedding_model": self.embedding_model,
            "embedding": self.embedding,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]):
        return Experience(
            session_id=d["session_id"],
            experience_text=d["experience_text"],
            raw_experience_path=d["raw_experience_path"],
            embedding_model=d["embedding_model"] if "embedding_model" in d else None,
            embedding=d["embedding"] if "embedding" in d else [],
        )


class ExperienceConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("experience")

        self.experience_dir = self._get_path(
            "experience_dir",
            os.path.join(self.src.app_base_path, "experience"),
        )
        self.default_exp_prompt_path = self._get_path(
            "default_exp_prompt_path",
            os.path.join(
                os.path.dirname(__file__),
                "default_exp_prompt.yaml",
            ),
        )
        self.retrieve_threshold = self._get_float("retrieve_threshold", 0.2)


class ExperienceGenerator:
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

        self.default_prompt_template = read_yaml(self.config.default_exp_prompt_path)["content"]

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
            if target_role == "Planner":  # For Planner, keep all messages for global view
                return
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
        raw_exp_file_path = os.path.join(self.config.experience_dir, f"raw_exp_{session_id}.yaml")
        conversation = read_yaml(raw_exp_file_path)

        conversation = self._preprocess_conversation_data(conversation, target_role)

        system_instruction = prompt if prompt else self.default_prompt_template
        prompt = [
            format_chat_message("system", system_instruction),
            format_chat_message("user", json.dumps(conversation)),
        ]
        summarized_experience = self.llm_api.chat_completion(prompt)["content"]

        return summarized_experience

    def refresh(
        self,
        target_role: Literal["Planner", "CodeInterpreter"],
        prompt: Optional[str] = None,
    ):
        if not os.path.exists(self.config.experience_dir):
            raise ValueError(f"Experience directory {self.config.experience_dir} does not exist.")

        exp_files = os.listdir(self.config.experience_dir)
        conv_session_ids = [
            os.path.splitext(os.path.basename(exp_file))[0].split("_")[2]
            for exp_file in exp_files
            if exp_file.startswith("raw_exp")
        ]

        handcrafted_session_ids = [
            os.path.splitext(os.path.basename(exp_file))[0].split("_")[2]
            for exp_file in exp_files
            if exp_file.startswith("handcrafted_exp")
        ]

        session_ids = conv_session_ids + handcrafted_session_ids

        if len(session_ids) == 0:
            warnings.warn(
                "No raw experience found. "
                "Please type #SAVE AS EXP in the chat window to save raw experience"
                "or write handcrafted experience.",
            )
            return

        to_be_embedded = []
        for idx, session_id in enumerate(session_ids):
            exp_file_name = f"{target_role}_exp_{session_id}.yaml"
            # if the experience file already exists and the embedding is valid, skip
            if exp_file_name in os.listdir(self.config.experience_dir):
                exp_file_path = os.path.join(self.config.experience_dir, exp_file_name)
                experience = read_yaml(exp_file_path)
                if (
                    experience["embedding_model"] == self.llm_api.embedding_service.config.embedding_model
                    and len(experience["embedding"]) > 0
                ):
                    continue
            else:
                # otherwise, summarize the experience and save it
                if session_id in conv_session_ids:
                    summarized_experience = self.summarize_experience(session_id, prompt, target_role)
                    experience_obj = Experience(
                        experience_text=summarized_experience,
                        session_id=session_id,
                        raw_experience_path=os.path.join(
                            self.config.experience_dir,
                            f"raw_exp_{session_id}.yaml",
                        ),
                    )
                else:
                    handcrafted_exp_file_path = os.path.join(
                        self.config.experience_dir,
                        f"handcrafted_exp_{session_id}.yaml",
                    )
                    experience_obj = Experience.from_dict(read_yaml(handcrafted_exp_file_path))
                self.experience_list.append(experience_obj)
                to_be_embedded.append(idx)
                self.logger.info("Experience created. Experience files number: {}".format(len(session_ids)))

        if len(to_be_embedded) == 0:
            return
        else:
            exp_embeddings = self.llm_api.get_embedding_list(
                [exp.experience_text for i, exp in enumerate(self.experience_list) if i in to_be_embedded],
            )
            for i, idx in enumerate(to_be_embedded):
                self.experience_list[idx].embedding = exp_embeddings[i]
                self.experience_list[idx].embedding_model = self.llm_api.embedding_service.config.embedding_model

        for exp in self.experience_list:
            experience_file_path = os.path.join(self.config.experience_dir, f"{target_role}_exp_{exp.session_id}.yaml")
            write_yaml(experience_file_path, exp.to_dict())
        self.logger.info("Experience obj saved.")

    def load_experience(
        self,
        target_role: Literal["Planner", "CodeInterpreter"],
    ):
        if not os.path.exists(self.config.experience_dir):
            raise ValueError(f"Experience directory {self.config.experience_dir} does not exist.")

        exp_files = [
            exp_file
            for exp_file in os.listdir(self.config.experience_dir)
            if exp_file.startswith(f"{target_role}_exp_")
        ]
        if len(exp_files) == 0:
            warnings.warn(
                f"No experience found for {target_role}."
                f" Please type #SAVE AS EXP in the chat window to save experience.",
            )
            return

        for exp_file in exp_files:
            exp_file_path = os.path.join(self.config.experience_dir, exp_file)
            experience = read_yaml(exp_file_path)
            if (
                experience["embedding_model"] != self.llm_api.embedding_service.config.embedding_model
                or len(experience["embedding"]) == 0
            ):
                raise ValueError(
                    "The embedding model of the experience is not the same as the current one."
                    "Please re-summarize and generatr embedding for the experience.",
                    "Please cd to the `script` directory and "
                    "run `python -m experience_mgt --refresh` to refresh the experience.",
                )
            else:
                self.experience_list.append(Experience(**experience))

    def retrieve_experience(self, user_query: str) -> List[Tuple[Experience, float]]:
        user_query_embedding = np.array(self.llm_api.get_embedding(user_query))

        similarities = []

        for experience in self.experience_list:
            if experience.embedding_model != self.llm_api.embedding_service.config.embedding_model:
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
        self.logger.info(f"Retrieved {len(selected_experiences)} experiences.")
        self.logger.info(f"Retrieved experiences: {[exp.session_id for exp, sim in selected_experiences]}")
        return selected_experiences

    def delete_experience(self, session_id: str, target_role: Literal["Planner", "CodeInterpreter"] = "Planner"):
        exp_file_name = f"{target_role}_exp_{session_id}.yaml"
        if exp_file_name in os.listdir(self.config.experience_dir):
            os.remove(os.path.join(self.config.experience_dir, exp_file_name))
            self.logger.info(f"Experience {exp_file_name} deleted.")
        else:
            self.logger.info(f"Experience {exp_file_name} not found.")

    def delete_raw_experience(self, session_id: str):
        exp_file_name = f"raw_exp_{session_id}.yaml"
        if exp_file_name in os.listdir(self.config.experience_dir):
            os.remove(os.path.join(self.config.experience_dir, exp_file_name))
            self.logger.info(f"Raw Experience {exp_file_name} deleted.")
        else:
            self.logger.info(f"Raw Experience {exp_file_name} not found.")
