import json
import os

import yaml

head = """The quiz for the agent is as follows:
====================================================================================================
"""

tail = """====================================================================================================

Ask the agent to complete the code between `###<SOLUTION>` and `###</SOLUTION>`, 
run it successfully, and present the code to you. 
Your request should contain all the information of the quiz above, especially the example input and output.

If the agent forget to include the `SOLUTION` comments, you should remind the agent to include them.
Once you know the `solution.py` file is ready, you must stop the conversation by saying `TASK_FINISHED`.
You should not help the agent to complete the code or provide any hints beyond the quiz above.
"""


def preprocess(original_prompt: str):
    _prompt = original_prompt.replace(
        "A:\n<code>\n",
        "I have writen my code as follows and you need to complete it to solve the problem:\n"
        "```python\n%%writefile solution.py # make sure this as the first line of code\n",
    )

    _prompt = _prompt.replace(
        "</code>\n",
        "###<SOLUTION>\n",
    )

    _prompt = _prompt.replace(
        "BEGIN SOLUTION\n<code>\n",
        "###</SOLUTION>\n```\n",
    )

    return head + _prompt + tail


jsonl_path = r"D:\DS-1000-main\simplified\data\ds1000.jsonl\ds1000.jsonl"
case_path = r"d:\ds-1000-cases"

evaluation_code = open("evaluate.py", "r").read()
case_yaml = yaml.safe_load(open("case.yaml", "r"))

for line in open(jsonl_path, "r"):
    case = json.loads(line)
    prompt = case["prompt"]
    reference_code = case["reference_code"]
    metadata = case["metadata"]
    code_context = case["code_context"]
    dependencies = [metadata["library"].lower()]
    problem_id = str(metadata["problem_id"])

    os.makedirs(os.path.join(case_path, problem_id), exist_ok=True)
    with open(os.path.join(case_path, problem_id, "prompt.txt"), "w", encoding="utf-8") as f:
        f.write(preprocess(prompt))
    with open(os.path.join(case_path, problem_id, "reference_code.py"), "w", encoding="utf-8") as f:
        f.write(reference_code)
    with open(os.path.join(case_path, problem_id, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f)
    with open(os.path.join(case_path, problem_id, "code_context.py"), "w", encoding="utf-8") as f:
        f.write(code_context)

    case_yaml["scoring_points"][0]["eval_code"] = evaluation_code
    case_yaml["task_description"] = preprocess(prompt)
    case_yaml["dependencies"] = dependencies
    with open(os.path.join(case_path, problem_id, "case.yaml"), "w", encoding="utf-8") as f:
        yaml.safe_dump(case_yaml, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
