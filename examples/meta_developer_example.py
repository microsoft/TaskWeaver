# examples/meta_developer_example.py

import logging
from taskweaver.ext_role.meta_developer.meta_developer import MetaDeveloper
from taskweaver.ext_role.meta_developer.analyzer import Analyzer
from taskweaver.ext_role.meta_developer.generator import Generator
from taskweaver.ext_role.meta_developer.debugger import Debugger

def main():
    """
    Demonstrates the usage of the MetaDeveloper role by executing the three phases:
    Analysis, Generation, and Debugging, to develop a simple application.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("MetaDeveloperExample")

    # Initialize the MetaDeveloper role
    logger.info("Initializing MetaDeveloper role...")
    meta_developer = MetaDeveloper()

    # Define a simple task description
    task_description = "Analyze, generate, and debug a simple Python project."

    # Phase 1: Analysis
    logger.info("Starting Analysis Phase...")
    analyzer = Analyzer()
    analysis_result = analyzer.analyze(task_description)
    logger.info(f"Analysis Result: {analysis_result}")

    # Phase 2: Generation
    logger.info("Starting Generation Phase...")
    generator = Generator()
    generation_result = generator.generate(analysis_result)
    logger.info(f"Generation Result: {generation_result}")

    # Phase 3: Debugging
    logger.info("Starting Debugging Phase...")
    debugger = Debugger()
    debugging_result = debugger.debug(generation_result)
    logger.info(f"Debugging Result: {debugging_result}")

    # Final Output
    logger.info("MetaDeveloper Example Completed.")
    logger.info("Summary of Results:")
    logger.info(f"1. Analysis Result: {analysis_result}")
    logger.info(f"2. Generation Result: {generation_result}")
    logger.info(f"3. Debugging Result: {debugging_result}")

if __name__ == "__main__":
    main()
