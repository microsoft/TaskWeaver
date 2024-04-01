import os
import sys
import warnings
from typing import Optional, Tuple

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

warnings.filterwarnings("ignore")

import pandas as pd
import yaml
from evaluator import Evaluator, ScoringPoint, VirtualUser

from taskweaver.app.app import TaskWeaverApp


class TaskWeaverVirtualUser(VirtualUser):
    def __init__(self, init_query: str, app_dir: str, config_var: Optional[dict] = None):
        super().__init__(init_query)

        self.app = TaskWeaverApp(app_dir=app_dir, config=config_var)
        self.session = self.app.get_session()

    def get_reply_from_agent(self, message: str) -> str:
        response_round = self.session.send_message(
            message,
            event_handler=None,
        )
        return response_round.post_list[-1].message

    def close(self):
        self.app.stop()


def auto_evaluate_for_taskweaver(
    eval_case_file_path: str,
) -> Tuple[float, float]:
    with open(eval_case_file_path, "r") as f:
        eval_meta_data = yaml.safe_load(f)

    app_dir = eval_meta_data["app_dir"]
    config_var = eval_meta_data.get("config_var", None)
    init_query = eval_meta_data["user_query"]

    taskweaver_vuser = TaskWeaverVirtualUser(init_query, app_dir, config_var)
    taskweaver_evaluator = Evaluator()

    chat_history = taskweaver_vuser.talk_with_agent()

    score_points = eval_meta_data["scoring_points"]
    score_points = [ScoringPoint(**score_point) for score_point in score_points]
    score, normalized_score = taskweaver_evaluator.evaluate(init_query, chat_history, score_points)

    taskweaver_vuser.close()

    return score, normalized_score


def batch_auto_evaluate_for_taskweaver(
    result_file_path: str,
    eval_case_dir: str,
    flush_result_file: bool = False,
):
    if not os.path.exists(result_file_path):
        df = pd.DataFrame(columns=["case_file", "score", "normalized_score"])
        df.to_csv(result_file_path, index=False)

    results = pd.read_csv(result_file_path)
    evaluated_case_files = results["case_file"].tolist()
    if flush_result_file:
        evaluated_case_files = []
    print(f"Evaluated case files: {evaluated_case_files}")
    eval_config_files = os.listdir(eval_case_dir)
    print(f"Eval config files in case dir: {eval_config_files}")

    for eval_config_file in eval_config_files:
        if eval_config_file in evaluated_case_files:
            print(f"Skip {eval_config_file} because it has been evaluated.")
            continue
        print("------------Start evaluating------------", eval_config_file)
        eval_case_file_path = os.path.join(eval_case_dir, eval_config_file)

        score, normalized_score = auto_evaluate_for_taskweaver(eval_case_file_path)
        new_res_row = pd.DataFrame(
            {
                "case_file": [eval_config_file],
                "score": [score],
                "normalized_score": [normalized_score],
            },
        )
        results = pd.concat([results, new_res_row], ignore_index=True)

        print("------------Finished evaluating------------", eval_config_file)

        results.to_csv(result_file_path, index=False)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Taskweaver auto evaluation script")
    parser.add_argument(
        "-m",
        "--mode",
        choices=["single", "batch"],
        required=True,
        help="Evaluation mode, single for evaluating a single case, " "batch for evaluating a batch of cases",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        required=True,
        help="Path to the evaluation case file or directory containing evaluation case files",
    )
    parser.add_argument(
        "-r",
        "--result",
        type=str,
        default="sample_case_results.csv",
        help="Path to the result file for batch evaluation mode",
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=None,
        help="Interrupt threshold for multi-round chat",
    )
    parser.add_argument(
        "-flush",
        "--flush",
        action="store_true",
        help="Flush the result file",
    )

    args = parser.parse_args()

    if args.mode == "single":
        score, normalized_score = auto_evaluate_for_taskweaver(args.file)
        print(f"Score: {score}, Normalized score: {normalized_score}")
    elif args.mode == "batch":
        batch_auto_evaluate_for_taskweaver(
            args.result,
            args.file,
            flush_result_file=args.flush,
        )
