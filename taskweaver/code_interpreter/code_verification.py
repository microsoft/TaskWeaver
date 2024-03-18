import ast
import re
from typing import List, Optional, Tuple

from injector import inject


class FunctionCallValidator(ast.NodeVisitor):
    @inject
    def __init__(
        self,
        lines: List[str],
        allowed_modules: Optional[List[str]] = None,
        blocked_modules: Optional[List[str]] = None,
        allowed_functions: Optional[List[str]] = None,
        blocked_functions: Optional[List[str]] = None,
        allowed_variables: Optional[List[str]] = None,
    ):
        self.lines = lines
        self.errors = []
        self.allowed_modules = allowed_modules
        self.blocked_modules = blocked_modules
        assert (
            allowed_modules is None or blocked_modules is None
        ), "Only one of allowed_modules or blocked_modules can be set."
        self.blocked_functions = blocked_functions
        self.allowed_functions = allowed_functions
        assert (
            allowed_functions is None or blocked_functions is None
        ), "Only one of allowed_functions or blocked_functions can be set."
        self.allowed_variables = allowed_variables

    def _is_allowed_function_call(self, func_name: str) -> bool:
        if self.allowed_functions is not None:
            if len(self.allowed_functions) > 0:
                return func_name in self.allowed_functions
            return False
        if self.blocked_functions is not None:
            if len(self.blocked_functions) > 0:
                return func_name not in self.blocked_functions
            return True
        return True

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            function_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            function_name = node.func.attr
        else:
            raise ValueError(f"Unsupported function call: {node.func}")

        if not self._is_allowed_function_call(function_name):
            self.errors.append(
                f"Error on line {node.lineno}: {self.lines[node.lineno - 1]} "
                f"=> Function '{function_name}' is not allowed.",
            )

    def _is_allowed_module_import(self, mod_name: str) -> bool:
        if self.allowed_modules is not None:
            if len(self.allowed_modules) > 0:
                return mod_name in self.allowed_modules
            return False
        if self.blocked_modules is not None:
            if len(self.blocked_modules) > 0:
                return mod_name not in self.blocked_modules
            return True
        return True

    def visit_Import(self, node):
        for alias in node.names:
            if "." in alias.name:
                module_name = alias.name.split(".")[0]
            else:
                module_name = alias.name

            if not self._is_allowed_module_import(module_name):
                self.errors.append(
                    f"Error on line {node.lineno}: {self.lines[node.lineno - 1]} "
                    f"=> Importing module '{module_name}' is not allowed. ",
                )

    def visit_ImportFrom(self, node):
        if "." in node.module:
            module_name = node.module.split(".")[0]
        else:
            module_name = node.module

        if not self._is_allowed_module_import(module_name):
            self.errors.append(
                f"Error on line {node.lineno}: {self.lines[node.lineno - 1]} "
                f"=>  Importing from module '{node.module}' is not allowed.",
            )

    def _is_allowed_variable(self, var_name: str) -> bool:
        if self.allowed_variables is not None:
            if len(self.allowed_variables) > 0:
                return var_name in self.allowed_variables
            return False
        return True

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                variable_name = target.id
            else:
                self.errors.append(
                    f"Error on line {node.lineno}: {self.lines[node.lineno - 1]} "
                    "=> Complex assignments are not allowed.",
                )
                continue

            if not self._is_allowed_variable(variable_name):
                self.errors.append(
                    f"Error on line {node.lineno}: {self.lines[node.lineno - 1]} "
                    f"=> Assigning to {variable_name} is not allowed.",
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


def code_snippet_verification(
    code_snippet: str,
    code_verification_on: bool = False,
    allowed_modules: Optional[List[str]] = None,
    blocked_modules: Optional[List[str]] = None,
    allowed_functions: Optional[List[str]] = None,
    blocked_functions: Optional[List[str]] = None,
    allowed_variables: Optional[List[str]] = None,
) -> Optional[List[str]]:
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
        validator = FunctionCallValidator(
            lines=processed_lines,
            allowed_modules=allowed_modules,
            blocked_modules=blocked_modules,
            allowed_functions=allowed_functions,
            blocked_functions=blocked_functions,
            allowed_variables=allowed_variables,
        )
        validator.visit(tree)
        errors.extend(validator.errors)
        return errors
    except SyntaxError as e:
        return [f"Syntax error: {e}"]
