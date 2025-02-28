"""
Configuration file for the MetaDeveloper role in TaskWeaver.

This file defines the parameters and options available for customizing the behavior
of the MetaDeveloper role. Users can modify these settings to tailor the role's
functionality to their specific project requirements.
"""

import logging

class MetaDeveloperConfig:
    """
    Configuration class for the MetaDeveloper role.
    """

    # Enable or disable specific phases
    ENABLE_ANALYSIS_PHASE = True
    ENABLE_GENERATION_PHASE = True
    ENABLE_DEBUGGING_PHASE = True

    # Logging configuration
    ENABLE_LOGGING = True  # Enable or disable logging
    LOGGING_LEVEL = logging.INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Analysis phase settings
    ANALYSIS_MAX_DEPTH = 10  # Maximum depth for codebase traversal
    ANALYSIS_INCLUDE_TESTS = False  # Whether to include test files in the analysis

    # Debugging phase settings
    DEBUGGING_MAX_RETRIES = 3  # Maximum number of retries for debugging

    # Generation phase settings
    GENERATION_TEMPLATE_PATH = "templates/"  # Path to code generation templates
    GENERATION_STRICT_MODE = True  # Enforce strict adherence to coding standards

    # Debugging phase settings
    DEBUGGING_ENABLE_SYNTAX_CHECK = True  # Enable syntax validation for generated code
    DEBUGGING_ENABLE_STATIC_ANALYSIS = True  # Enable static analysis for generated code

    # General settings
    MAX_ITERATIONS = 5  # Maximum number of iterations for the development cycle
    SAVE_REPORTS = True  # Whether to save analysis and debugging reports to disk
    REPORTS_DIRECTORY = "reports/"  # Directory to save reports

    @classmethod
    def to_dict(cls):
        """
        Returns the configuration as a dictionary.

        This method can be used to dynamically access the configuration
        parameters in other parts of the codebase.
        """
        return {
            "ENABLE_ANALYSIS_PHASE": cls.ENABLE_ANALYSIS_PHASE,
            "ENABLE_GENERATION_PHASE": cls.ENABLE_GENERATION_PHASE,
            "ENABLE_DEBUGGING_PHASE": cls.ENABLE_DEBUGGING_PHASE,
            "ENABLE_LOGGING": cls.ENABLE_LOGGING,
            "LOGGING_LEVEL": cls.LOGGING_LEVEL,
            "ANALYSIS_MAX_DEPTH": cls.ANALYSIS_MAX_DEPTH,
            "ANALYSIS_INCLUDE_TESTS": cls.ANALYSIS_INCLUDE_TESTS,
            "DEBUGGING_MAX_RETRIES": cls.DEBUGGING_MAX_RETRIES,
            "GENERATION_TEMPLATE_PATH": cls.GENERATION_TEMPLATE_PATH,
            "GENERATION_STRICT_MODE": cls.GENERATION_STRICT_MODE,
            "DEBUGGING_ENABLE_SYNTAX_CHECK": cls.DEBUGGING_ENABLE_SYNTAX_CHECK,
            "DEBUGGING_ENABLE_STATIC_ANALYSIS": cls.DEBUGGING_ENABLE_STATIC_ANALYSIS,
            "MAX_ITERATIONS": cls.MAX_ITERATIONS,
            "SAVE_REPORTS": cls.SAVE_REPORTS,
            "REPORTS_DIRECTORY": cls.REPORTS_DIRECTORY,
        }
```

### Step 4: Review the Code
1. **Functionality**:
   - The `MetaDeveloperConfig` class encapsulates all configuration parameters for the `MetaDeveloper` role.
   - The `to_dict` method provides a way to access the configuration as a dictionary, ensuring compatibility with other parts of the framework.
2. **Conventions**:
   - The file adheres to Python's conventions and the style used in the `TaskWeaver` codebase.
   - Logging levels and other parameters are defined using standard Python practices.
3. **Completeness**:
   - All required parameters are implemented, and the file is fully functional.
   - No placeholders or TODOs are left in the code.
4. **Extensibility**:
   - The configuration is designed to be easily extensible, allowing users to add new parameters as needed.

### Final Output
Here is the full content of the `taskweaver/ext_role/meta_developer/config.py` file:

```
"""
Configuration file for the MetaDeveloper role in TaskWeaver.

This file defines the parameters and options available for customizing the behavior
of the MetaDeveloper role. Users can modify these settings to tailor the role's
functionality to their specific project requirements.
"""

import logging

class MetaDeveloperConfig:
    """
    Configuration class for the MetaDeveloper role.
    """

    # Enable or disable specific phases
    ENABLE_ANALYSIS_PHASE = True
    ENABLE_GENERATION_PHASE = True
    ENABLE_DEBUGGING_PHASE = True

    # Logging configuration
    LOGGING_LEVEL = logging.INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Analysis phase settings
    ANALYSIS_MAX_DEPTH = 10  # Maximum depth for codebase traversal
    ANALYSIS_INCLUDE_TESTS = False  # Whether to include test files in the analysis

    # Generation phase settings
    GENERATION_TEMPLATE_PATH = "templates/"  # Path to code generation templates
    GENERATION_STRICT_MODE = True  # Enforce strict adherence to coding standards

    # Debugging phase settings
    DEBUGGING_ENABLE_SYNTAX_CHECK = True  # Enable syntax validation for generated code
    DEBUGGING_ENABLE_STATIC_ANALYSIS = True  # Enable static analysis for generated code

    # General settings
    MAX_ITERATIONS = 5  # Maximum number of iterations for the development cycle
    SAVE_REPORTS = True  # Whether to save analysis and debugging reports to disk
    REPORTS_DIRECTORY = "reports/"  # Directory to save reports

    @classmethod
    def to_dict(cls):
        """
        Returns the configuration as a dictionary.

        This method can be used to dynamically access the configuration
        parameters in other parts of the codebase.
        """
        return {
            "ENABLE_ANALYSIS_PHASE": cls.ENABLE_ANALYSIS_PHASE,
            "ENABLE_GENERATION_PHASE": cls.ENABLE_GENERATION_PHASE,
            "ENABLE_DEBUGGING_PHASE": cls.ENABLE_DEBUGGING_PHASE,
            "LOGGING_LEVEL": cls.LOGGING_LEVEL,
            "ANALYSIS_MAX_DEPTH": cls.ANALYSIS_MAX_DEPTH,
            "ANALYSIS_INCLUDE_TESTS": cls.ANALYSIS_INCLUDE_TESTS,
            "GENERATION_TEMPLATE_PATH": cls.GENERATION_TEMPLATE_PATH,
            "GENERATION_STRICT_MODE": cls.GENERATION_STRICT_MODE,
            "DEBUGGING_ENABLE_SYNTAX_CHECK": cls.DEBUGGING_ENABLE_SYNTAX_CHECK,
            "DEBUGGING_ENABLE_STATIC_ANALYSIS": cls.DEBUGGING_ENABLE_STATIC_ANALYSIS,
            "MAX_ITERATIONS": cls.MAX_ITERATIONS,
            "SAVE_REPORTS": cls.SAVE_REPORTS,
            "REPORTS_DIRECTORY": cls.REPORTS_DIRECTORY,
        }