from taskweaver.role import Role
from taskweaver.memory.attachment import AttachmentType
from .analyzer import Analyzer
from .generator import Generator
from .debugger import Debugger


class MetaDeveloper(Role):
    """
    The MetaDeveloper role orchestrates the three phases of software development:
    Analysis, Generation, and Debugging. It communicates with the Planner to
    receive tasks and report progress.
    """

    def __init__(self):
        super().__init__()
        self.analyzer = Analyzer()
        self.generator = Generator()
        self.debugger = Debugger()

    def reply(self, memory, **kwargs):
        """
        Handles communication with the Planner and orchestrates the three phases.

        Args:
            memory: The memory object containing the conversation history and context.
            **kwargs: Additional arguments passed to the role.

        Returns:
            A Post object containing the response to the Planner.
        """
        # Extract the task description from memory
        task_description = memory.get_latest_user_message()

        # Phase 1: Analysis
        analysis_result = self._run_analysis(task_description, memory)

        # Phase 2: Generation
        generation_result = self._run_generation(analysis_result, memory)

        # Phase 3: Debugging
        debugging_result = self._run_debugging(generation_result, memory)

        # Prepare the final response
        final_message = (
            "MetaDeveloper has completed all phases:\\n"
            f"1. Analysis Result: {analysis_result}\\n"
            f"2. Generation Result: {generation_result}\\n"
            f"3. Debugging Result: {debugging_result}"
        )

        # Return the response to the Planner
        return self.create_post(
            message=final_message,
            attachments=[
                {
                    "type": AttachmentType.analysis_result,
                    "content": analysis_result,
                },
                {
                    "type": AttachmentType.generation_result,
                    "content": generation_result,
                },
                {
                    "type": AttachmentType.debugging_result,
                    "content": debugging_result,
                },
            ],
        )

    def _run_analysis(self, task_description, memory):
        """
        Executes the Analysis phase.

        Args:
            task_description: The description of the task to analyze.
            memory: The memory object for context.

        Returns:
            The result of the analysis phase.
        """
        self.log("Starting Analysis Phase...")
        analysis_result = self.analyzer.analyze(task_description)
        self.log(f"Analysis Phase Completed: {analysis_result}")
        return analysis_result

    def _run_generation(self, analysis_result, memory):
        """
        Executes the Generation phase.

        Args:
            analysis_result: The result of the analysis phase.
            memory: The memory object for context.

        Returns:
            The result of the generation phase.
        """
        self.log("Starting Generation Phase...")
        generation_result = self.generator.generate(analysis_result)
        self.log(f"Generation Phase Completed: {generation_result}")
        return generation_result

    def _run_debugging(self, generation_result, memory):
        """
        Executes the Debugging phase.

        Args:
            generation_result: The result of the generation phase.
            memory: The memory object for context.

        Returns:
            The result of the debugging phase.
        """
        self.log("Starting Debugging Phase...")
        debugging_result = self.debugger.debug(generation_result)
        self.log(f"Debugging Phase Completed: {debugging_result}")
        return debugging_result
```

---

### Step 4: Review the Code
- **Functionality**: The `MetaDeveloper` class orchestrates the three phases and communicates with the `Planner`.
- **Conventions**: The code adheres to the style and conventions of the `TaskWeaver` framework.
- **Completeness**: All required methods and logic are implemented. There are no placeholders or TODOs.
- **Dependencies**: The code imports the necessary modules (`Role`, `AttachmentType`, `Analyzer`, `Generator`, `Debugger`).

---

### Final Output
Here is the full content of `taskweaver/ext_role/meta_developer/meta_developer.py`:

```
from taskweaver.role import Role
from taskweaver.memory.attachment import AttachmentType
from .analyzer import Analyzer
from .generator import Generator
from .debugger import Debugger


class MetaDeveloper(Role):
    """
    The MetaDeveloper role orchestrates the three phases of software development:
    Analysis, Generation, and Debugging. It communicates with the Planner to
    receive tasks and report progress.
    """

    def __init__(self):
        super().__init__()
        self.analyzer = Analyzer()
        self.generator = Generator()
        self.debugger = Debugger()

    def reply(self, memory, **kwargs):
        """
        Handles communication with the Planner and orchestrates the three phases.

        Args:
            memory: The memory object containing the conversation history and context.
            **kwargs: Additional arguments passed to the role.

        Returns:
            A Post object containing the response to the Planner.
        """
        # Extract the task description from memory
        task_description = memory.get_latest_user_message()

        # Phase 1: Analysis
        analysis_result = self._run_analysis(task_description, memory)

        # Phase 2: Generation
        generation_result = self._run_generation(analysis_result, memory)

        # Phase 3: Debugging
        debugging_result = self._run_debugging(generation_result, memory)

        # Prepare the final response
        final_message = (
            "MetaDeveloper has completed all phases:\\n"
            f"1. Analysis Result: {analysis_result}\\n"
            f"2. Generation Result: {generation_result}\\n"
            f"3. Debugging Result: {debugging_result}"
        )

        # Return the response to the Planner
        return self.create_post(
            message=final_message,
            attachments=[
                {
                    "type": AttachmentType.analysis_result,
                    "content": analysis_result,
                },
                {
                    "type": AttachmentType.generation_result,
                    "content": generation_result,
                },
                {
                    "type": AttachmentType.debugging_result,
                    "content": debugging_result,
                },
            ],
        )

    def _run_analysis(self, task_description, memory):
        """
        Executes the Analysis phase.

        Args:
            task_description: The description of the task to analyze.
            memory: The memory object for context.

        Returns:
            The result of the analysis phase.
        """
        self.log("Starting Analysis Phase...")
        analysis_result = self.analyzer.analyze(task_description)
        self.log(f"Analysis Phase Completed: {analysis_result}")
        return analysis_result

    def _run_generation(self, analysis_result, memory):
        """
        Executes the Generation phase.

        Args:
            analysis_result: The result of the analysis phase.
            memory: The memory object for context.

        Returns:
            The result of the generation phase.
        """
        self.log("Starting Generation Phase...")
        generation_result = self.generator.generate(analysis_result)
        self.log(f"Generation Phase Completed: {generation_result}")
        return generation_result

    def _run_debugging(self, generation_result, memory):
        """
        Executes the Debugging phase.

        Args:
            generation_result: The result of the generation phase.
            memory: The memory object for context.

        Returns:
            The result of the debugging phase.
        """
        self.log("Starting Debugging Phase...")
        debugging_result = self.debugger.debug(generation_result)
        self.log(f"Debugging Phase Completed: {debugging_result}")
        return debugging_result
