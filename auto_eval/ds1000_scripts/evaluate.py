import re


def extract_solution_code(file_path):
    with open(file_path, "r") as file:
        solution_code = file.read()

    # Find the part between the solution comments using a regular expression
    solution_regex = re.compile(r"###<SOLUTION>(.*?)###</SOLUTION>", re.DOTALL)
    solution_match = solution_regex.search(solution_code)
    return solution_match.group(1).strip()


from code_context import test_execution

try:
    test_execution(extract_solution_code("solution.py"))
    return True
except Exception as e:
    print(f"failed to run test case, {e}")
    return False
