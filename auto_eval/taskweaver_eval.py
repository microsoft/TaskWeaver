import json
import os
import warnings
from typing import Any, Optional

warnings.filterwarnings("ignore")

import pandas as pd
import yaml
from evaluator import Evaluator, ScoringPoint

from taskweaver.app.app import TaskWeaverApp


def format_output(response_obj: Any) -> str:
    assert hasattr(response_obj, "to_dict"), "to_dict method is not found"
    formatted_output = json.dumps(response_obj.to_dict())
    return formatted_output


def auto_evaluate_for_taskweaver(
    eval_case_file_path: str,
    interrupt_threshold: Optional[float] = None,
    event_handler: Optional[callable] = None,
) -> [float, float]:
    with open(eval_case_file_path, "r") as f:
        eval_meta_data = yaml.safe_load(f)

    app_dir = eval_meta_data["app_dir"]
    config_var = eval_meta_data.get("config_var", None)

    app = TaskWeaverApp(app_dir=app_dir, config=config_var)
    session = app.get_session()

    taskweaver_evaluator = Evaluator()

    score_list = []
    for idx, eval_query in enumerate(eval_meta_data["eval_query"]):
        user_query = eval_query["user_query"]
        print(f"Round-{idx} user query:\n", user_query)

        response_round = session.send_message(
            user_query,
            event_handler=event_handler if event_handler is not None else lambda x, y: print(f"{x}:\n{y}"),
        )

        post_index = eval_query.get("post_index", None)
        scoring_point_data = eval_query.get("scoring_points", None)
        if scoring_point_data is None:
            print("No scoring points are provided. Skip evaluation for this round.")
            continue
        scoring_points = []
        for scoring_point in scoring_point_data:
            scoring_point = ScoringPoint(**scoring_point)
            scoring_points.append(scoring_point)

        if isinstance(post_index, int):
            response = format_output(response_round.post_list[post_index])
        elif post_index is None:
            response = format_output(response_round)
        else:
            raise ValueError("Invalid post_index")
        print("Taskweaver response:\n", response)
        score, normalized_score = taskweaver_evaluator.evaluate(user_query, response, scoring_points)
        score_list.append((idx, score, normalized_score))
        if interrupt_threshold is not None and interrupt_threshold > 0:
            if normalized_score < interrupt_threshold:
                print(
                    f"Interrupted conversation testing "
                    f"because the normalized score is lower than the threshold {interrupt_threshold}.",
                )
                break

    return score_list


def batch_auto_evaluate_for_taskweaver(
    result_file_path: str,
    eval_case_dir: str,
    flush_result_file: bool = False,
    interrupt_threshold: Optional[float] = None,
):
    if not os.path.exists(result_file_path):
        df = pd.DataFrame(columns=["case_file", "round", "score", "normalized_score"])
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
        score_list = auto_evaluate_for_taskweaver(
            eval_case_file_path,
            interrupt_threshold=interrupt_threshold,
        )
        for idx, score, normalized_score in score_list:
            print(f"Round-{idx} score: {score}, normalized score: {normalized_score}")
            new_res_row = pd.DataFrame(
                {
                    "case_file": eval_config_file,
                    "round": idx,
                    "score": score,
                    "normalized_score": normalized_score,
                },
                index=[0],
            )
            results = pd.concat([results, new_res_row], ignore_index=True)

        print("------------Finished evaluating------------", eval_config_file)

        results.to_csv(result_file_path, index=False)


if __name__ == "__main__":
    # run single case
    eval_case_file_path = "cases/complicated_task_stock_forecasting.yaml"
    score_list = auto_evaluate_for_taskweaver(eval_case_file_path, interrupt_threshold=None)
    for idx, score, normalized_score in score_list:
        print(f"Round-{idx} score: {score}, normalized score: {normalized_score}")

    # run batch cases
    result_file_path = "sample_case_results.csv"
    case_file_dir = "cases"
    batch_auto_evaluate_for_taskweaver(
        result_file_path,
        case_file_dir,
        flush_result_file=False,
        interrupt_threshold=None,
    )
