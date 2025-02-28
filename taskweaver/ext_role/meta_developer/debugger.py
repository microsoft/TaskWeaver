import logging


class Debugger:
    """
    The Debugger class is responsible for debugging and improving the generated application code.
    It provides custom debugging tools tailored to the application's needs.
    """

    def __init__(self):
        """
        Initializes the Debugger with a logger.
        """
        self.logger = logging.getLogger(self.__class__.__name__)

    def debug(self, generation_result: dict):
        """
        Debugs the generated application code and identifies potential issues.

        Args:
            generation_result (dict): The result of the code generation phase, including the generated code.

        Returns:
            dict: A dictionary containing debugging results and suggestions for improvement.
        """
        self.logger.info("Starting debugging phase...")
        self.logger.debug(f"Generation result: {generation_result}")

        # Extract the generated code
        generated_code = generation_result.get("generated_code", "")
        if not generated_code:
            self.logger.error("No generated code found in the generation result.")
            return {"status": "error", "message": "No generated code to debug."}

        # Perform syntax validation
        syntax_issues = self._validate_syntax(generated_code)

        # Perform static analysis
        static_analysis_results = self._perform_static_analysis(generated_code)

        # Generate debugging suggestions
        suggestions = self._generate_suggestions(syntax_issues, static_analysis_results)

        self.logger.info("Debugging phase completed.")
        return {
            "status": "success",
            "syntax_issues": syntax_issues,
            "static_analysis_results": static_analysis_results,
            "suggestions": suggestions,
        }

    def _validate_syntax(self, code: str):
        """
        Validates the syntax of the generated code.

        Args:
            code (str): The generated Python code as a string.

        Returns:
            list: A list of syntax issues found in the code.
        """
        self.logger.debug("Validating syntax of the generated code...")
        issues = []
        try:
            # Parse the code to check for syntax errors
            compile(code, "<string>", "exec")
            self.logger.debug("Syntax validation successful.")
        except SyntaxError as e:
            self.logger.error(f"Syntax error found: {e}")
            issues.append({"line": e.lineno, "message": str(e)})

        return issues

    def _perform_static_analysis(self, code: str):
        """
        Performs static analysis on the generated code to identify potential issues.

        Args:
            code (str): The generated Python code as a string.

        Returns:
            list: A list of static analysis results.
        """
        self.logger.debug("Performing static analysis on the generated code...")
        analysis_results = []

        # Example: Check for unused imports
        import ast

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if not self._is_import_used(alias.name, tree):
                            message = f"Unused import: {alias.name}"
                            self.logger.warning(message)
                            analysis_results.append({"line": node.lineno, "message": message})
        except Exception as e:
            self.logger.error(f"Error during static analysis: {e}")
            analysis_results.append({"error": str(e)})

        return analysis_results

    def _is_import_used(self, import_name: str, tree: ast.AST):
        """
        Checks if an imported module or name is used in the code.

        Args:
            import_name (str): The name of the imported module or symbol.
            tree (ast.AST): The abstract syntax tree of the code.

        Returns:
            bool: True if the import is used, False otherwise.
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == import_name:
                return True
        return False

    def _generate_suggestions(self, syntax_issues: list, static_analysis_results: list):
        """
        Generates debugging suggestions based on the identified issues.

        Args:
            syntax_issues (list): A list of syntax issues found in the code.
            static_analysis_results (list): A list of static analysis results.

        Returns:
            list: A list of suggestions for improving the code.
        """
        self.logger.debug("Generating debugging suggestions...")
        suggestions = []

        if syntax_issues:
            suggestions.append("Fix the syntax errors to ensure the code can run without issues.")

        if static_analysis_results:
            suggestions.append("Review the static analysis results and address the identified issues.")

        if not syntax_issues and not static_analysis_results:
            suggestions.append("No issues found. The code is ready for execution.")

        return suggestions
