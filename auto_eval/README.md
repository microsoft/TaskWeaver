# How to run auto evaluation

## Quick start

We have prepared some example tasks to run auto evaluation.
You can run them by following the steps below:

1. Complete the `evaluator_config.json` (referring to the schema in `evaluator_config_template.json`) under the `auto_eval` folder and the  `taskweaver_config.json` under the `taskweaver` folder.
2. Go to the `auto_eval` folder.
3. Run the command below to start the auto evaluation for single case.
```bash
python taskweaver_eval.py -m single -p cases/echo
```
Or run the command below to start the auto evaluation for multiple cases.
```bash
python taskweaver_eval.py -m batch -p ./cases
```

## Parameters

- -m/--mode: specifies the evaluation mode, which can be `single` or `batch`. 
- -p/--path: specifies the path to the test case file or directory containing test case files. 
- -r/--result: specifies the path to the result file for batch evaluation mode. This parameter is only valid in batch mode. The default value is `sample_case_results.csv`.
- -f/--fresh: specifies whether to flush the result file. This parameter is only valid in batch mode. The default value is `False`, which means that the evaluated cases will not be loaded again. If you want to re-evaluate the cases, you can set this parameter to `True`.


## How to create a sample task

A sample task can be configured in the yaml file that contains the following fields:

- config_var (optional): set the configuration values for TaskWeaver if needed.
- app_dir: the path to the project directory for TaskWeaver.
- dependencies: the list of Python package dependencies that are required to run the task.
If current environment is not compatible with the dependencies, it will report an error.
- data_files: the list of data files that are required to run the task.
- task_description: the description of the task.
- scoring_points:
  - score_point: describes the criteria of the agent's response
  - weight: the value that determines how important that criterion is
  - eval_code (optional): evaluation code that will be run to determine if the criterion is met. In this case, this scoring point will not be evaluated using LLM.

> 💡 for the `eval_code` field, you can use the variable `chat_history` in your evaluation code snippet.
It is a list of [Messages objects of Langchain](https://python.langchain.com/docs/modules/model_io/concepts#messages) that contain the chat history between the virtual user and the agent.
The `eval_code` should use the `assert` statement to check the criterion.


## How to evaluate other Agents

Our evaluation framework is designed to be generic and can be used to evaluate other agents besides TaskWeaver.
If you want to evaluate other agents, you should follow the steps below.

1. Create a new python file under `auto_eval`, create a new class and inherit the `VirtualUser` in `evaluator.py`.
Just like below:
```python
from evaluator import VirtualUser

class YourVirtualUser(VirtualUser):
      def __init__(self, task_description: str, app_dir: str, config_var: Optional[dict] = None):
        super().__init__(task_description)
        """
        Initialize the VirtualUser.
        """
        ...

    def get_reply_from_agent(self, message: str) -> str:
        # Custom code to get the reply from your agent.
```

2. You can get the config values from the `config_var` parameter in the `__init__` method to set the config values for your agent if needed.
3. Implement the `get_reply_from_agent` method to get the reply from your agent.
4. Develop the evaluation logic.
5. Use the `Evaluator` class to evaluate the agent's response.
   1. load the task case
   2. check the package version
   3. create the VirtualUser and Evaluator
   4. assign the task to the agent via the virtual user
   5. evaluate the agent's response

```python
from evaluator import Evaluator, ScoringPoint, VirtualUser
from utils import check_package_version, load_task_case

def auto_evaluate_for_your_agent(
    eval_case_dir: str,
) -> Tuple[float, float]:
    # Load the task case
    eval_meta_data = load_task_case(eval_case_dir)
    app_dir = eval_meta_data["app_dir"]
    config_var = eval_meta_data.get("config_var", None)
    task_description = eval_meta_data["task_description"]
    dependencies = eval_meta_data.get("dependencies", [])
    data_files = eval_meta_data.get("data_files", [])
    
    # Check the package version
    for dependency in dependencies:
        check_package_version(dependency)
    
    # Create the VirtualUser and Evaluator
    vuser = YourVirtualUser(task_description, app_dir, config_var)
    evaluator = Evaluator()
    
    # assign the task to the agent via the virtual user
    chat_history = vuser.talk_with_agent()
    
    # Evaluate the agent's response
    score_points = eval_meta_data["scoring_points"]
    score_points = [ScoringPoint(**score_point) for score_point in score_points]
    score, normalized_score = evaluator.evaluate(task_description, chat_history, score_points)
    
    return score, normalized_score
```
