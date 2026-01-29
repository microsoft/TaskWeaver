import ast
import re
from typing import List, Optional, Tuple

from injector import inject

# Security-sensitive functions that can be used for dynamic attribute access bypasses
DANGEROUS_BUILTINS = [
    "getattr",
    "setattr",
    "delattr",
    "vars",
    "globals",
    "locals",
    "__getattribute__",
    "__setattr__",
    "__delattr__",
    "__dict__",
    "__class__",
    "__bases__",
    "__subclasses__",
    "__mro__",
    "__builtins__",
]


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
        function_name = None
        if isinstance(node.func, ast.Name):
            function_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            function_name = node.func.attr
        elif isinstance(node.func, ast.Subscript):
            # Block subscript-based function calls like obj["method"]()
            # This is a potential security bypass pattern
            self.errors.append(
                f"Error on line {node.lineno}: {self.lines[node.lineno - 1]} "
                f"=> Subscript-based function calls are not allowed for security reasons.",
            )
            self.generic_visit(node)
            return
        elif isinstance(node.func, ast.Call):
            # Block chained calls that might be used for dynamic resolution
            # e.g., getattr(obj, 'method')()
            self.generic_visit(node)
            return
        else:
            # Block any other unrecognized call patterns for security
            self.errors.append(
                f"Error on line {node.lineno}: {self.lines[node.lineno - 1]} "
                f"=> Unrecognized function call pattern is not allowed for security reasons.",
            )
            self.generic_visit(node)
            return

        # Check against allowed/blocked function lists if configured
        if self.allowed_functions is not None or self.blocked_functions is not None:
            if function_name and not self._is_allowed_function_call(function_name):
                self.errors.append(
                    f"Error on line {node.lineno}: {self.lines[node.lineno - 1]} "
                    f"=> Function '{function_name}' is not allowed.",
                )

        # Always check for dynamic attribute access functions that can bypass security
        if function_name in DANGEROUS_BUILTINS:
            self.errors.append(
                f"Error on line {node.lineno}: {self.lines[node.lineno - 1]} "
                f"=> Function '{function_name}' is blocked as it can be used to bypass security checks.",
            )

        self.generic_visit(node)

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
        if self.allowed_modules is not None or self.blocked_modules is not None:
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
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if self.allowed_modules is not None or self.blocked_modules is not None:
            if node.module and "." in node.module:
                module_name = node.module.split(".")[0]
            else:
                module_name = node.module

            if module_name and not self._is_allowed_module_import(module_name):
                self.errors.append(
                    f"Error on line {node.lineno}: {self.lines[node.lineno - 1]} "
                    f"=>  Importing from module '{node.module}' is not allowed.",
                )
        self.generic_visit(node)

    def _is_allowed_variable(self, var_name: str) -> bool:
        if self.allowed_variables is not None:
            if len(self.allowed_variables) > 0:
                return var_name in self.allowed_variables
            return False
        return True

    def visit_Assign(self, node: ast.Assign):
        if self.allowed_variables is not None:
            for target in node.targets:
                variable_names = []
                if isinstance(target, ast.Name):
                    variable_names.append(target.id)
                else:
                    for name in ast.walk(target):
                        if isinstance(name, ast.Name):
                            variable_names.append(name.id)
                for variable_name in variable_names:
                    if not self._is_allowed_variable(variable_name):
                        self.errors.append(
                            f"Error on line {node.lineno}: {self.lines[node.lineno - 1]} "
                            f"=> Assigning to {variable_name} is not allowed.",
                        )
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript):
        """Check for dictionary-based attribute access that could bypass security.

        Patterns like obj.__dict__["method"] or obj["__class__"] can be used
        to bypass attribute-based security checks.
        """
        # Check if the subscript key is a dangerous dunder attribute
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            key_value = node.slice.value
            if key_value in DANGEROUS_BUILTINS or key_value.startswith("__"):
                self.errors.append(
                    f"Error on line {node.lineno}: {self.lines[node.lineno - 1]} "
                    f"=> Subscript access to '{key_value}' is blocked for security reasons.",
                )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        """Check for dangerous attribute access patterns.

        Direct access to dunder attributes like __class__, __dict__, etc.
        can be used to bypass security measures.
        """
        attr_name = node.attr
        if attr_name in DANGEROUS_BUILTINS:
            self.errors.append(
                f"Error on line {node.lineno}: {self.lines[node.lineno - 1]} "
                f"=> Attribute access to '{attr_name}' is blocked for security reasons.",
            )
        self.generic_visit(node)

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
