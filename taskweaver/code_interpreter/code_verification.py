import ast
import re
from typing import List, Optional, Tuple

from injector import inject

from taskweaver.module.tracer import get_current_span, tracer


class FunctionCallValidator(ast.NodeVisitor):
    @inject
    def __init__(
        self,
        lines: List[str],
        allowed_modules: List[str],
        blocked_functions: List[str],
    ):
        self.lines = lines
        self.errors = []
        self.allowed_modules = allowed_modules
        self.blocked_functions = blocked_functions

    def visit_Call(self, node):
        if len(self.blocked_functions) > 0:
            if isinstance(node.func, ast.Name):
                function_name = node.func.id
                if function_name in self.blocked_functions:
                    self.errors.append(
                        f"Error on line {node.lineno}: {self.lines[node.lineno-1]} "
                        f"=> Function '{node.func.id}' is not allowed.",
                    )
                    return False
                return True
            elif isinstance(node.func, ast.Attribute):
                function_name = node.func.attr
                if function_name in self.blocked_functions:
                    self.errors.append(
                        f"Error on line {node.lineno}: {self.lines[node.lineno-1]} "
                        f"=> Function '{function_name}' is not allowed.",
                    )
                    return False
                return True
            else:
                return True

    def visit_Import(self, node):
        for alias in node.names:
            if "." in alias.name:
                module_name = alias.name.split(".")[0]
            else:
                module_name = alias.name
            if len(self.allowed_modules) > 0 and module_name not in self.allowed_modules:
                self.errors.append(
                    f"Error on line {node.lineno}: {self.lines[node.lineno-1]} "
                    f"=> Importing module '{module_name}' is not allowed. ",
                )
            elif len(self.allowed_modules) == 0:
                self.errors.append(
                    f"Error on line {node.lineno}: {self.lines[node.lineno-1]} "
                    f"=> Importing module '{module_name}' is not allowed. ",
                )

    def visit_ImportFrom(self, node):
        if "." in node.module:
            module_name = node.module.split(".")[0]
        else:
            module_name = node.module
        if len(self.allowed_modules) > 0 and module_name not in self.allowed_modules:
            self.errors.append(
                f"Error on line {node.lineno}: {self.lines[node.lineno-1]} "
                f"=>  Importing from module '{node.module}' is not allowed.",
            )
        elif len(self.allowed_modules) == 0:
            self.errors.append(
                f"Error on line {node.lineno}: {self.lines[node.lineno-1]} "
                f"=>  Importing from module '{node.module}' is not allowed.",
            )

    def generic_visit(self, node):
        super().generic_visit(node)


def format_code_correction_message() -> str:
    return (
        "The generated code has been verified and some errors are found. "
        "If you think you can fix the problem by rewriting the code, "
        "please do it and try again.\n"
        "Otherwise, please explain the problem to me."
    )


def separate_magics_and_code(input_code: str) -> Tuple[List[str], str, List[str]]:
    line_magic_pattern = re.compile(r"^\s*%\s*[a-zA-Z_]\w*")
    cell_magic_pattern = re.compile(r"^\s*%%\s*[a-zA-Z_]\w*")
    shell_command_pattern = re.compile(r"^\s*!")

    magics = []
    python_code = []
    package_install_commands = []

    lines = input_code.splitlines()
    inside_cell_magic = False

    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue

        if inside_cell_magic:
            magics.append(line)
            if not line.strip():
                inside_cell_magic = False
            continue
        if line_magic_pattern.match(line) or shell_command_pattern.match(line):
            # Check if the line magic or shell command is a package installation command
            if "pip install" in line or "conda install" in line:
                package_install_commands.append(line)
            else:
                magics.append(line)
        elif cell_magic_pattern.match(line):
            inside_cell_magic = True
            magics.append(line)
        else:
            python_code.append(line)
    python_code_str = "\n".join(python_code)
    return magics, python_code_str, package_install_commands


@tracer.start_as_current_span("CodeVerification.code_snippet_verification")
def code_snippet_verification(
    code_snippet: str,
    code_verification_on: bool = False,
    allowed_modules: List[str] = [],
    blocked_functions: List[str] = [],
) -> Optional[List[str]]:
    current_span = get_current_span()
    current_span.set_attribute("code_verification_on", code_verification_on)
    if code_verification_on:
        current_span.set_attribute("allowed_modules", str(allowed_modules))
        current_span.set_attribute("blocked_functions", str(blocked_functions))

    if not code_verification_on:
        return None
    errors = []
    try:
        magics, python_code, _ = separate_magics_and_code(code_snippet)
        if len(magics) > 0:
            errors.append(f"Magic commands except package install are not allowed. Details: {magics}")
        tree = ast.parse(python_code)

        processed_lines = []
        for line in python_code.splitlines():
            if not line.strip() or line.strip().startswith("#"):
                continue
            processed_lines.append(line)
        validator = FunctionCallValidator(processed_lines, allowed_modules, blocked_functions)
        validator.visit(tree)
        errors.extend(validator.errors)
        return errors
    except SyntaxError as e:
        # print(f"Syntax error: {e}")
        return [f"Syntax error: {e}"]
