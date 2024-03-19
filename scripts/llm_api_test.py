import argparse
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from injector import Injector

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.llm import LLMApi, format_chat_message
from taskweaver.logging import LoggingModule

parser = argparse.ArgumentParser()

parser.add_argument(
    "--project_dir",
    type=str,
    default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project"),
)

parser.add_argument("--query", type=str, default="Hello!")

args = parser.parse_args()


def LLM_API_test():
    app_injector = Injector([LoggingModule])
    app_config = AppConfigSource(
        config_file_path=os.path.join(
            args.project_dir,
            "taskweaver_config.json",
        ),
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    llm_api = app_injector.create_object(LLMApi)

    llm_stream = llm_api.chat_completion_stream(
        messages=[format_chat_message(role="user", message=args.query)],
        use_smoother=True,
    )

    for msg in llm_stream:
        print(msg["content"], end="")


if __name__ == "__main__":
    LLM_API_test()
