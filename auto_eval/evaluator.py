import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

import yaml
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain.schema.messages import HumanMessage, SystemMessage

PROMPT_FILE_PATH = os.path.join(os.path.dirname(__file__), "evaluator_prompt.yaml")


@dataclass
class ScoringPoint:
    score_point: str
    weight: float
    eval_code: Optional[str] = None


def load_config():
    with open("evaluator_config.json", "r") as f:
        evaluator_config = json.load(f)
    return evaluator_config


def get_config(config: Dict[str, str], var_name: str) -> str:
    val = os.environ.get(var_name, None)
    if val is not None:
        return val
    elif var_name in config.keys():
        return config.get(var_name)
    else:
        raise ValueError(f"Config value {var_name} is not found")


def config_llm(config: Dict[str, str]) -> Union[ChatOpenAI, AzureChatOpenAI]:
    api_type = get_config(config, "llm.api_type")
    if api_type == "azure":
        model = AzureChatOpenAI(
            azure_endpoint=get_config(config, "llm.api_base"),
            openai_api_key=get_config(config, "llm.api_key"),
            openai_api_version=get_config(config, "llm.api_version"),
            azure_deployment=get_config(config, "llm.model"),
            temperature=0,
            verbose=True,
        )
    elif api_type == "openai":
        model = ChatOpenAI(
            openai_api_key=get_config(config, "llm.api_key"),
            model_name=get_config(config, "llm.model"),
            temperature=0,
            verbose=True,
        )
    else:
        raise ValueError("Invalid API type. Please check your config file.")
    return model


class Evaluator(object):
    def __init__(self):
        with open(PROMPT_FILE_PATH, "r") as file:
            self.prompt_data = yaml.safe_load(file)
        self.prompt = self.prompt_data["instruction_template"].format(
            response_schema=self.prompt_data["response_schema"],
        )
        self.config = load_config()
        self.llm_model = config_llm(self.config)

    @staticmethod
    def format_input(user_query: str, agent_responses: str, scoring_point: ScoringPoint) -> str:
        return "The agent's output is: " + agent_responses + "\n" + "The statement is: " + scoring_point.score_point

    @staticmethod
    def parse_output(response: str) -> bool:
        try:
            structured_response = json.loads(response)
            is_hit = structured_response["is_hit"].lower()
            return True if is_hit == "yes" else False
        except Exception as e:
            if "yes" in response.lower():
                return True
            elif "no" in response.lower():
                return False
            else:
                raise e

    def score(self, user_query: str, agent_response: str, scoring_point: ScoringPoint) -> float:
        if scoring_point.eval_code is not None:
            code = scoring_point.eval_code
            agent_response = json.loads(agent_response)
            indented_code = "\n".join([f"    {line}" for line in code.strip().split("\n")])
            func_code = (
                f"def check_agent_response(agent_response):\n"
                f"{indented_code}\n"
                f"result = check_agent_response(agent_response)"
            )
            local_vars = locals()
            exec(func_code, None, local_vars)
            return local_vars["result"]
        else:
            messages = [
                SystemMessage(content=self.prompt),
                HumanMessage(content=self.format_input(user_query, agent_response, scoring_point)),
            ]

            response = self.llm_model.invoke(messages).content

            is_hit = self.parse_output(response)
            return is_hit

    def evaluate(self, user_query, agent_response, scoring_points: List[ScoringPoint]) -> [float, float]:
        max_score = sum([scoring_point.weight for scoring_point in scoring_points])
        score = 0

        for idx, scoring_point in enumerate(scoring_points):
            single_score = int(self.score(user_query, agent_response, scoring_point)) * scoring_point.weight
            print(f"single_score: {single_score} for {idx+1}-scoring_point: {scoring_point.score_point}")
            score += single_score
        normalized_score = score / max_score

        return score, normalized_score
