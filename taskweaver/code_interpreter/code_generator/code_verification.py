import ast
import builtins
import re
from _ast import Name
from typing import List, Optional, Tuple

from injector import inject

from taskweaver.config.module_config import ModuleConfig


class CodeVerificationConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("code_verification")
        self.code_verification_on = self._get_bool("code_verification_on", False)
        self.plugin_only = self._get_bool("plugin_only", False)
        self.allowed_modules = self._get_list(
            "allowed_modules",
            ["pandas", "matplotlib", "numpy", "sklearn", "scipy", "seaborn", "datetime", "typing"],
        )

        if self.plugin_only:
            self.code_verification_on = True
            self.allowed_modules = []


allowed_builtins = [name for name, obj in vars(builtins).items() if callable(obj)]


class FunctionCallValidator(ast.NodeVisitor):
    @inject
    def __init__(self, lines: List[str], config: CodeVerificationConfig, plugin_list: List[str]):
        self.lines = lines
        self.config = config
        self.plugin_list = plugin_list
        self.errors = []
        self.plugin_return_values = []

    def visit_Call(self, node):
        if self.config.plugin_only:
            if isinstance(node.func, ast.Name):
                function_name = node.func.id
                if function_name not in self.plugin_list and function_name not in allowed_builtins:
                    self.errors.append(
                        f"Error on line {node.lineno}: {self.lines[node.lineno-1]} "
                        f"=> Function '{node.func.id}' is not allowed.",
                    )
                    return False
                return True
            elif isinstance(node.func, ast.Attribute):
                function_name = node.func.attr
                if function_name not in allowed_builtins and function_name not in self.plugin_list:
                    self.errors.append(
                        f"Error on line {node.lineno}: {self.lines[node.lineno-1]} "
                        f"=> Function '{function_name}' is not allowed.",
                    )
                    return False
                return True
            else:
                self.errors.append(
                    f"Error on line {node.lineno}: {self.lines[node.lineno-1]} " f"=> Function call is not allowed.",
                )
                return False

    def visit_Import(self, node):
        if len(self.config.allowed_modules) > 0:
            for alias in node.names:
                if "." in alias.name:
                    module_name = alias.name.split(".")[0]
                else:
                    module_name = alias.name
                if len(self.config.allowed_modules) > 0 and module_name not in self.config.allowed_modules:
                    self.errors.append(
                        f"Error on line {node.lineno}: {self.lines[node.lineno-1]} "
                        f"=> Importing module '{module_name}' is not allowed. ",
                    )

    def visit_ImportFrom(self, node):
        if len(self.config.allowed_modules) > 0:
            if "." in node.module:
                module_name = node.module.split(".")[0]
            else:
                module_name = node.module
            if len(self.config.allowed_modules) > 0 and module_name not in self.config.allowed_modules:
                self.errors.append(
                    f"Error on line {node.lineno}: {self.lines[node.lineno-1]} "
                    f"=>  Importing from module '{node.module}' is not allowed.",
                )

    def visit_FunctionDef(self, node):
        if self.config.plugin_only:
            self.errors.append(
                f"Error on line {node.lineno}: {self.lines[node.lineno-1]} => Defining new functions is not allowed.",
            )

    def visit_Assign(self, node):
        if self.config.plugin_only:
            if isinstance(node.value, ast.Call):
                is_allowed_call = self.visit_Call(node.value)
                if not is_allowed_call:
                    return
                if isinstance(node.targets[0], ast.Tuple):
                    for elt in node.targets[0].elts:
                        if isinstance(elt, ast.Name):
                            self.plugin_return_values.append(elt.id)
                elif isinstance(node.targets[0], ast.Name):
                    self.plugin_return_values.append(node.targets[0].id)
                # print(self.plugin_return_values)
            else:
                self.errors.append(f"Error: Unsupported assignment on line {node.lineno}.")
                self.generic_visit(node)

    def visit_Name(self, node: Name):
        if self.config.plugin_only:
            if node.id not in self.plugin_return_values:
                self.errors.append(
                    f"Error on line {node.lineno}: {self.lines[node.lineno-1]} => "
                    "Only return values of plugins calls can be used.",
                )
            # self.generic_visit(node)

    def generic_visit(self, node):
        if self.config.plugin_only and not isinstance(
            node,
            (ast.Call, ast.Assign, ast.Import, ast.ImportFrom, ast.Expr, ast.Module, ast.Name),
        ):
            if isinstance(node, ast.Tuple):
                for elt in node.elts:
                    self.visit(elt)
            else:
                error_message = (
                    f"Error on line {node.lineno}: {self.lines[node.lineno-1]} => "
                    "Codes except plugin calls are not allowed."
                )
                self.errors.append(error_message)

        else:
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
    plugin_list: List[str],
    config: CodeVerificationConfig,
) -> Optional[List[str]]:
    if not config.code_verification_on:
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
        validator = FunctionCallValidator(processed_lines, config, plugin_list)
        validator.visit(tree)
        errors.extend(validator.errors)
        return errors
    except SyntaxError as e:
        # print(f"Syntax error: {e}")
        return [f"Syntax error: {e}"]
