import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

import yaml
from langchain.load.dump import dumps
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage
from langchain_community.chat_models import ChatOpenAI
from langchain_openai import AzureChatOpenAI

EVALUATOR_PROMPT_FILE_PATH = os.path.join(os.path.dirname(__file__), "evaluator_prompt.yaml")
VIRTUAL_USER_PROMPT_FILE_PATH = os.path.join(os.path.dirname(__file__), "virtual_user_prompt.yaml")


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
        raise ValueError(f"Config value {var_name} is not found in evaluator_config.json or environment variables.")


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


class VirtualUser:
    def __init__(self, task_description: str):
        with open(VIRTUAL_USER_PROMPT_FILE_PATH, "r") as file:
            self.prompt_data = yaml.safe_load(file)
        self.stop_keyword = self.prompt_data["stop_keyword"]
        self.prompt_template = self.prompt_data["instruction_template"]

        self.config = load_config()
        self.llm_model = config_llm(self.config)

        self.task_description = task_description
        self.kick_off_message = self.prompt_data["kick_off_message"]

        self.max_rounds = self.config.get("max_rounds", 15)

    def talk_with_agent(self):
        sys_message = self.prompt_template.format(
            task_description=self.task_description,
            stop_keyword=self.stop_keyword,
            kick_off_message=self.kick_off_message,
        )
        round_num = 0
        chat_history = [SystemMessage(content=sys_message)]
        print(f"Task: {self.task_description}")
        user_query = self.get_reply_from_vuser(self.kick_off_message, chat_history)
        print(f"User: {user_query}")
        while True:
            agent_response = self.get_reply_from_agent(user_query)
            print(f"Agent: {agent_response}")
            vuser_response = self.get_reply_from_vuser(agent_response, chat_history)
            print(f"User: {vuser_response}")
            if self.stop_keyword in vuser_response:
                break
            user_query = vuser_response
            round_num += 1
            if round_num >= self.max_rounds:
                print("Max rounds reached. Stopping conversation.")
                break
        return chat_history

    def get_reply_from_vuser(
        self,
        message: str,
        chat_history: List[Union[AIMessage, HumanMessage, SystemMessage]],
    ) -> str:
        chat_history.append(HumanMessage(content=message))
        response = self.llm_model.invoke(chat_history).content
        chat_history.append(AIMessage(content=response))
        return response

    def get_reply_from_agent(self, message: str) -> str:
        raise NotImplementedError


class Evaluator(object):
    def __init__(self):
        with open(EVALUATOR_PROMPT_FILE_PATH, "r") as file:
            self.prompt_data = yaml.safe_load(file)
        self.prompt = self.prompt_data["instruction_template"].format(
            response_schema=self.prompt_data["response_schema"],
        )
        self.config = load_config()
        self.llm_model = config_llm(self.config)

    @staticmethod
    def format_input(
        task_description: str,
        chat_history: List[Union[AIMessage, HumanMessage, SystemMessage]],
        scoring_point: ScoringPoint,
    ) -> str:
        chat_history_text = dumps(chat_history)
        return (
            f"The task description is: {task_description}\n"
            f"The chat history between user and agent is: {chat_history_text}\n"
            f"The statement is: {scoring_point.score_point}"
        )

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

    def score(
        self,
        task_description: str,
        chat_history: List[Union[AIMessage, HumanMessage, SystemMessage]],
        scoring_point: ScoringPoint,
    ) -> float:
        if scoring_point.eval_code is not None:
            code = scoring_point.eval_code
            indented_code = "\n".join([f"    {line}" for line in code.strip().split("\n")])
            func_code = (
                f"def check_agent_response(chat_history):\n"
                f"{indented_code}\n"
                f"result = check_agent_response(chat_history)"
            )
            local_vars = locals()
            exec(func_code, None, local_vars)
            return local_vars["result"]
        else:
            messages = [
                SystemMessage(content=self.prompt),
                HumanMessage(content=self.format_input(task_description, chat_history, scoring_point)),
            ]

            response = self.llm_model.invoke(messages).content

            is_hit = self.parse_output(response)
            return is_hit

    def evaluate(
        self,
        task_description: str,
        chat_history: List[Union[AIMessage, HumanMessage, SystemMessage]],
        scoring_points: List[ScoringPoint],
    ) -> [float, float]:
        max_score = sum([scoring_point.weight for scoring_point in scoring_points])
        score = 0

        for idx, scoring_point in enumerate(scoring_points):
            single_score = int(self.score(task_description, chat_history, scoring_point)) * scoring_point.weight
            print(f"single_score: {single_score} for {idx+1}-scoring_point: {scoring_point.score_point}")
            score += single_score
        normalized_score = score / max_score

        return score, normalized_score
