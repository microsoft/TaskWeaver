import os
import ast
import logging


class Analyzer:
    """
    The Analyzer class is responsible for analyzing the project's codebase,
    extracting structural and functional information, and generating analysis
    reports to assist in understanding the project.
    """

    def __init__(self):
        """
        Initializes the Analyzer with a logger.
        """
        self.logger = logging.getLogger(self.__class__.__name__)

    def analyze(self, task_description: str):
        """
        Analyzes the project's codebase based on the provided task description.

        Args:
            task_description (str): A description of the task to analyze.

        Returns:
            dict: A structured result containing analysis details.
        """
        self.logger.info("Starting analysis phase...")
        self.logger.debug(f"Task description: {task_description}")

        # Simulate locating the project's root directory
        project_root = self._find_project_root()
        self.logger.debug(f"Project root directory: {project_root}")

        # Simulate analyzing Python files in the project
        analysis_results = self._analyze_codebase(project_root)

        # Generate a summary report
        report = self._generate_report(analysis_results)

        self.logger.info("Analysis phase completed.")
        return report

    def _find_project_root(self):
        """
        Simulates locating the project's root directory.

        Returns:
            str: The path to the project's root directory.
        """
        # For simplicity, assume the current working directory is the project root
        return os.getcwd()

    def _analyze_codebase(self, project_root):
        """
        Analyzes Python files in the project's codebase.

        Args:
            project_root (str): The root directory of the project.

        Returns:
            list: A list of dictionaries containing analysis details for each file.
        """
        analysis_results = []
        for root, _, files in os.walk(project_root):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    self.logger.debug(f"Analyzing file: {file_path}")
                    file_analysis = self._analyze_file(file_path)
                    analysis_results.append(file_analysis)
        return analysis_results

    def _analyze_file(self, file_path):
        """
        Analyzes a single Python file.

        Args:
            file_path (str): The path to the Python file.

        Returns:
            dict: A dictionary containing analysis details for the file.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            # Parse the file content into an abstract syntax tree (AST)
            tree = ast.parse(file_content)
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

            return {
                "file_path": file_path,
                "functions": functions,
                "classes": classes,
                "lines_of_code": len(file_content.splitlines()),
            }
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {e}")
            return {
                "file_path": file_path,
                "error": str(e),
            }

    def _generate_report(self, analysis_results):
        """
        Generates a summary report based on the analysis results.

        Args:
            analysis_results (list): A list of dictionaries containing analysis details.

        Returns:
            dict: A structured report summarizing the analysis.
        """
        total_files = len(analysis_results)
        total_lines = sum(result.get("lines_of_code", 0) for result in analysis_results if "lines_of_code" in result)
        total_functions = sum(len(result.get("functions", [])) for result in analysis_results)
        total_classes = sum(len(result.get("classes", [])) for result in analysis_results)

        report = {
            "summary": {
                "total_files": total_files,
                "total_lines_of_code": total_lines,
                "total_functions": total_functions,
                "total_classes": total_classes,
            },
            "details": analysis_results,
        }

        self.logger.debug(f"Generated report: {report}")
        return report