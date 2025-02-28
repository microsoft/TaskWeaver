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
    logger.info("Initializing the MetaDeveloper role to orchestrate the development phases...")
    meta_developer = MetaDeveloper()

    # Define a simple task description
    task_description = "Analyze, generate, and debug a simple Python project."

    # Phase 1: Analysis
    logger.info("Starting the Analysis Phase: Extracting structural and functional details from the codebase...")
    analyzer = Analyzer()
    try:
        analysis_result = analyzer.analyze(task_description)
        logger.info(f"Analysis Phase Completed Successfully. Result: {analysis_result}")
    except Exception as e:
        logger.error(f"Analysis Phase Failed. Error: {e}")
        return

    # Phase 2: Generation
    logger.info("Starting the Generation Phase: Creating new code based on the analysis results...")
    generator = Generator()
    try:
        generation_result = generator.generate(analysis_result)
        logger.info(f"Generation Phase Completed Successfully. Result: {generation_result}")
    except Exception as e:
        logger.error(f"Generation Phase Failed. Error: {e}")
        return

    # Phase 3: Debugging
    logger.info("Starting the Debugging Phase: Identifying and resolving issues in the generated code...")
    debugger = Debugger()
    try:
        debugging_result = debugger.debug(generation_result)
        logger.info(f"Debugging Phase Completed Successfully. Result: {debugging_result}")
    except Exception as e:
        logger.error(f"Debugging Phase Failed. Error: {e}")
        return

    # Final Output
    logger.info("MetaDeveloper Example Completed.")
    logger.info("Summary of Results:")
    logger.info("===================================")
    logger.info(f"1. Analysis Result:\\n{analysis_result}")
    logger.info("-----------------------------------")
    logger.info(f"2. Generation Result:\\n{generation_result}")
    logger.info("-----------------------------------")
    logger.info(f"3. Debugging Result:\\n{debugging_result}")
    logger.info("===================================")

if __name__ == "__main__":
    main()