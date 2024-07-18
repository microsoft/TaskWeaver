import os
import shutil
import subprocess
import sys
import warnings
from typing import Optional, Tuple

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

warnings.filterwarnings("ignore")

import pandas as pd
from evaluator import Evaluator, ScoringPoint, VirtualUser
from utils import check_package_version, load_task_case

from taskweaver.app.app import TaskWeaverApp


class TaskWeaverVirtualUser(VirtualUser):
    def __init__(self, task_description: str, app_dir: str, config_var: Optional[dict] = None):
        super().__init__(task_description)

        self.app = TaskWeaverApp(app_dir=app_dir, config=config_var)
        self.session = self.app.get_session()
        self.session_id = self.session.session_id

    def get_reply_from_agent(self, message: str, verbose: bool = False) -> str:
        response_round = self.session.send_message(
            message,
            event_handler=None,
        )
        assert response_round.state != "failed", "Failed to get response from agent."
        if verbose:
            verbose_response = "\n Below are conversation details inside the Agent: \n"
            for post in response_round.post_list:
                message = f"{post.send_from} -> {post.send_to}: {post.message}"
                verbose_response += f"{message}\n"
                # uncomment the following code block if you want to see the attachments during the evaluation
                # for atta in post.attachment_list:
                #     atta_type = atta.type.value
                #     atta_content = atta.content
                #     if atta_type in  ["plan", "current_plan_step", "thought", "python",
                # "execution_status", "execution_result"]:
                #         atta_message = f"# {atta_type}: {atta_content}"
                #         verbose_response += f"  {atta_message}\n"
            return verbose_response
        return response_round.post_list[-1].message

    def close(self):
        self.app.stop()


def auto_evaluate_for_taskweaver(
    eval_case_dir: str,
) -> Tuple[float, float]:
    eval_meta_data = load_task_case(eval_case_dir)

    app_dir = eval_meta_data["app_dir"]
    config_var = eval_meta_data.get("config_var", None)
    task_description = eval_meta_data["task_description"]
    dependencies = eval_meta_data.get("dependencies", [])
    data_files = eval_meta_data.get("data_files", [])
    pre_command = eval_meta_data.get("pre_command", [])
    verbose = eval_meta_data.get("verbose", False)

    for dependency in dependencies:
        check_package_version(dependency)

    for command in pre_command:
        # run the command
        # subprocess.run(command, shell=True)
        result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # result = subprocess.check_output(command.split(" "), stderr=subprocess.STDOUT)
        if result.returncode == 0:
            print("Precommand executed successfully")
            print(result.stdout)
        else:
            print("Command failed")
            print(result.stderr)

    taskweaver_vuser = TaskWeaverVirtualUser(task_description, app_dir, config_var)
    taskweaver_evaluator = Evaluator()

    working_directory = os.path.join(app_dir, "workspace", "sessions", taskweaver_vuser.session_id, "cwd")

    for data_file in data_files:
        if not os.path.exists(os.path.join(eval_case_dir, data_file)):
            raise FileNotFoundError(f"Data file {data_file} is not found.")
        else:
            file_path = os.path.join(eval_case_dir, data_file)
            if os.path.isfile(file_path):
                shutil.copy(file_path, working_directory)
            else:
                shutil.copytree(file_path, os.path.join(working_directory, data_file))

    chat_history = taskweaver_vuser.talk_with_agent(verbose=verbose)

    score_points = eval_meta_data["scoring_points"]
    score_points = [ScoringPoint(**score_point) for score_point in score_points]
    score, normalized_score = taskweaver_evaluator.evaluate(
        task_description,
        chat_history,
        score_points,
        working_directory,
    )

    taskweaver_vuser.close()

    return score, normalized_score


def batch_auto_evaluate_for_taskweaver(
    result_file_path: str,
    eval_case_root: str,
    flush_result_file: bool = False,
    sleep_time: int = 0,
):
    if not os.path.exists(result_file_path):
        df = pd.DataFrame(columns=["case_file", "score", "normalized_score"])
        df.to_csv(result_file_path, index=False)

    results = pd.read_csv(result_file_path, dtype={"case_file": str})
    evaluated_case_files = [str(f) for f in results["case_file"].tolist()]
    if flush_result_file:
        evaluated_case_files = []
    print(f"Evaluated case files: {evaluated_case_files}")
    eval_config_dirs = os.listdir(eval_case_root)
    print(f"Eval config files in case dir: {eval_config_dirs}")

    for eval_case_dir in eval_config_dirs:
        if eval_case_dir in evaluated_case_files:
            print(f"Skip {eval_case_dir} because it has been evaluated.")
            continue
        print("------------Start evaluating------------", eval_case_dir)
        eval_case_dir_path = os.path.join(eval_case_root, eval_case_dir)

        score, normalized_score = auto_evaluate_for_taskweaver(eval_case_dir_path)
        new_res_row = pd.DataFrame(
            {
                "case_file": [eval_case_dir],
                "score": [score],
                "normalized_score": [normalized_score],
            },
        )
        results = pd.concat([results, new_res_row], ignore_index=True)

        print("------------Finished evaluating------------", eval_case_dir)

        results.to_csv(result_file_path, index=False)

        if sleep_time > 0:
            print(f"Sleeping for {sleep_time} seconds...")
            import time

            time.sleep(sleep_time)


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
        "-p",
        "--path",
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
        "-f",
        "--fresh",
        action="store_true",
        help="Flush the result file",
    )
    parser.add_argument(
        "-s",
        "--sleep",
        type=int,
        default=0,
        help="Sleep time between evaluations",
    )

    args = parser.parse_args()

    if args.mode == "single":
        score, normalized_score = auto_evaluate_for_taskweaver(args.path)
        print(f"Score: {score}, Normalized score: {normalized_score}")
    elif args.mode == "batch":
        batch_auto_evaluate_for_taskweaver(
            args.result,
            args.path,
            flush_result_file=args.fresh,
            sleep_time=args.sleep,
        )
