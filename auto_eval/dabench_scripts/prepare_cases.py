import json
import os
import shutil
import sys

import yaml

if __name__ == "__main__":
    jsonl_question_file = sys.argv[1]
    jsonl_label_file = sys.argv[2]
    data_file_path = sys.argv[3]
    case_path = sys.argv[4]

    questions = {}
    labels = {}

    with open(jsonl_question_file, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            _id = str(data["id"]).zfill(3)
            questions[_id] = data

    with open(jsonl_label_file, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            _id = str(data["id"]).zfill(3)
            labels[_id] = data

    case_yaml = yaml.safe_load(open("case.yaml", "r"))

    def format_description(question: dict):
        template = """
        # Task
        Load the file {file} and answer the following questions.
        
        # Question
        {question}
        
        # Constraints
        {constraints}
        
        # Format
        {format}
        """
        return template.format(
            file=question["file_name"],
            question=question["question"],
            constraints=question["constraints"],
            format=question["format"],
        )

    def format_score_points(_label: dict):
        score_points = []
        for answer in _label["common_answers"]:
            score_points.append(
                {
                    "score_point": f"The {answer[0]} is {answer[1]}",
                    "weight": 1,
                },
            )
        return score_points

    for _id in questions:
        question = questions[_id]
        label = labels[_id]

        case_yaml["data_files"] = [question["file_name"]]
        case_yaml["task_description"] = format_description(question)
        case_yaml["scoring_points"] = format_score_points(label)

        os.makedirs(os.path.join(case_path, _id), exist_ok=True)
        with open(os.path.join(case_path, _id, "case.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(case_yaml, f)
        # copy the data file
        data_file = os.path.join(data_file_path, question["file_name"])
        shutil.copy(data_file, os.path.join(case_path, _id, question["file_name"]))
