# How to run auto evaluation

## Quick start

We prepared some example queries to run auto evaluation.
You can run them by following the steps below.

1. complete the `evaluator_config.json` (referring to the schema in `evaluator_config_template.json`) under the `auto_eval` folder and the  `taskweaver_config.json` under the `taskweaver` folder.
2. cd to the `auto_eval` folder.
3. run the below command to start the auto evaluation for single case.
```bash
python taskweaver_eval.py -m single -f cases/init_say_hello.yaml
```
4. run the below command to start the auto evaluation for multiple cases.
```bash
python taskweaver_eval.py -m batch -f ./cases
```

## Parameters

- -m/--mode: specifies the evaluation mode, which can be either single or batch. 
- -f/--file: specifies the path to the test case file or directory containing test case files. 
- -r/--result: specifies the path to the result file for batch evaluation mode. This parameter is only valid in batch mode. The default value is `sample_case_results.csv`.
- -t/--threshold: specifies the interrupt threshold for multi-round chat evaluation. When the evaluation score of a certain round falls below this threshold, the evaluation will be interrupted. The default value is `None`, which means that no interrupt threshold is used.
- -flush/--flush: specifies whether to flush the result file. This parameter is only valid in batch mode. The default value is `False`, which means that the evaluated cases will not be loaded again. If you want to re-evaluate the cases, you can set this parameter to `True`.


## How to create a test case

A test case is a yaml file that contains the following fields:

- config_var(optional): set the config values for Taskweaver if needed.
- app_dir: the path to the project directory for Taskweaver.
- eval_query (a list, supports multiple queries)
  - user_query: the user query to be evaluated.
    - scoring_points:
      - score_point: describes the criteria of the agent's response
      - weight: the value that determines how important that criterion is
      - eval_code(optional): evaluation code that will be run to determine if the criterion is met. In this case, this scoring point will not be evaluated using LLM.
    - ...
  - ...
- post_index: the index of the `post_list` in response `round` that should be evaluated. If it is set to `null`, then the entire `round` will be evaluated.

