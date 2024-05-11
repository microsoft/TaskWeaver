import json
import os
import re
import sys

import yaml

head = """
The task is to complete the sample code described in the <TASK DESCRIPTION> block below.
Complete the code, run it successfully, and finally present the code back. 
Please "copy and paste" the following task description in your request to ensure 
that the task description is correct and complete.

<TASK DESCRIPTION>
"""

tail = """
</TASK DESCRIPTION>
"""


def replace_with_same_indent(original, target, replacement):
    last_line = original.split("\n")[-1]
    # Find the indentation of the original line
    indent_match = re.match(r"(\s*)", last_line)
    if indent_match:
        indentation = indent_match.group(1)
    else:
        indentation = ""

        # Split the replacement into lines and indent each line
    replacement_lines = replacement.splitlines()
    indented_replacement = "\n".join(indentation + line for line in replacement_lines)
    indented_replacement = indented_replacement.strip()

    # Replace the target string with the indented replacement
    pattern = re.escape(target)
    new_string = re.sub(pattern, indented_replacement, original, flags=re.MULTILINE)

    return new_string


def preprocess(original_prompt: str):
    _prompt = original_prompt.replace("Problem:", "# Problem")
    pattern = "A:\n+(.*)\n?<code>"
    instruction = None

    if "A:\n" in _prompt:
        match = re.search(pattern, _prompt)
        if match:
            solution_start = match.group(0)
            instruction = match.group(1).strip()
        else:
            raise ValueError("No match found")
    else:
        solution_start = None

    new_solution_start = (
        "# Solution\n"
        "The following is the solution code to the problem statement provided above.\n"
        "You must complete the code by filling in the missing parts between "
        "`### SOLUTION START` and `### SOLUTION END`.\n"
        "You must keep any code outside of `### SOLUTION START` and `### SOLUTION END` untouched.\n"
        "Once you have completed the code, run it to check if your solution is correct.\n"
        "Make sure you keep `### SOLUTION START` and `### SOLUTION END` along with your solution code.\n"
        "{instruction}\n"
        "\n"
        "```python\n"
    )

    if instruction is not None and len(instruction) > 5:
        new_solution_start = new_solution_start.format(
            instruction=f"The requirement for this task is to {instruction}",
        )
    else:
        new_solution_start = new_solution_start.format(instruction="")

    if solution_start is not None:
        _prompt = _prompt.replace(
            solution_start,
            new_solution_start,
        )
    else:
        _prompt = new_solution_start + _prompt

    if "</code>" in original_prompt:  # insertion case
        _prompt = _prompt.replace(
            "</code>\n",
            "### SOLUTION START\n",
        )

        _prompt = _prompt.replace(
            "BEGIN SOLUTION\n<code>",
            "### SOLUTION END\n" "```",
        )
    elif "    ### BEGIN SOLUTION" in original_prompt:
        if "def f(" in _prompt:
            last_line = _prompt.split("\n")[-2].replace("    # ", "")
        else:
            raise ValueError(original_prompt)

        _prompt = _prompt.replace(
            "    ### BEGIN SOLUTION",
            "    ### SOLUTION START\n    _result = ... # complete here\n   "
            " return _result\n    ### SOLUTION END\n" + last_line,
        )

    elif "\n# SOLUTION START" in original_prompt:
        _prompt = _prompt.replace(
            "# SOLUTION START",
            "### SOLUTION START\n...\n### SOLUTION END\n\n",
        )
    else:
        print(original_prompt)

    return head + _prompt + tail


def package_mapping(pkg: str):
    if pkg == "tensorflow":
        return "tensorflow-cpu"
    if pkg == "sklearn":
        return "scikit-learn"
    return pkg


if __name__ == "__main__":
    jsonl_path = sys.argv[1]
    case_path = sys.argv[2]
    case_yaml = yaml.safe_load(open("case.yaml", "r"))

    for line in open(jsonl_path, "r"):
        case = json.loads(line)
        prompt = case["prompt"]
        reference_code = case["reference_code"]
        metadata = case["metadata"]
        code_context = case["code_context"]
        dependencies = [package_mapping(metadata["library"].lower())]
        problem_id = str(metadata["problem_id"])

        if metadata["problem_id"] >= 817:
            continue
        # pad problem_id with 0s
        problem_id = problem_id.zfill(3)

        os.makedirs(os.path.join(case_path, problem_id), exist_ok=True)
        with open(os.path.join(case_path, problem_id, "prompt.txt"), "w", encoding="utf-8") as f:
            f.write(preprocess(prompt))
        with open(os.path.join(case_path, problem_id, "reference_code.py"), "w", encoding="utf-8") as f:
            f.write(reference_code)
        with open(os.path.join(case_path, problem_id, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f)
        with open(os.path.join(case_path, problem_id, f"code_context.py"), "w", encoding="utf-8") as f:
            f.write(code_context)

        case_yaml["task_description"] = preprocess(prompt)
        case_yaml["dependencies"] = dependencies
        with open(os.path.join(case_path, problem_id, "case.yaml"), "w", encoding="utf-8") as f:
            yaml.safe_dump(case_yaml, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
