# Auto Plugin Selection 

In TaskWeaver, we provide an auto plugin selection mechanism to dynamically select the best plugin for each user request.
It targets to solve the following two problems:

1. An excessive number of plugins may cause confusion for LLM, leading to inaccuracies in generating the correct code.
2. A large number of plugins could lead to increased token usage (potentially exceeding the token limit of LLM) and extended response time.

## Auto Plugin Selection Overview

Below is the overview workflow of the auto plugin selection mechanism.
![Auto Plugin Selection Overview](../../../.asset/APS.png)

NOTE: the automatic plugin selection mechanism is only activated during the code generation process in the Code Interpreter and does not affect the planning process of the Planner.

At the start of TaskWeaver initialization, the automatic plugin selector is activated to generate embedding vectors for all plugins, including their names and descriptions. 
The embedding vectors are created using the specified embedding model configured in the `taskweaver_config.json` file. 
For more information, please refer to the [embedding](embedding) documentation.

When the Planner sends a request to the Code Interpreter, the auto plugin selection mechanism will be triggered.
It will first generate an embedding vector for the request using the same embedding model.
Then, it will calculate the cosine similarity between the request embedding vector and the embedding vectors of all plugins.
It will select the top-k plugins with the highest cosine similarity scores and  load them into the `code_generator` prompt.

Upon completing the code generation, the `code_generator` employs one or more plugins to produce the desired code. 
We have established a plugin pool to store the plugins involved in the code generation process while filtering out any unused ones. 
During the subsequent automatic plugin selection phase, newly chosen plugins are appended to the existing ones. 


## Auto Plugin Selection Configuration
- `code_generator.enable_auto_plugin_selection`: Whether to enable auto plugin selection. The default value is `false`.
- `code_generator.auto_plugin_selection_topk`:	The number of auto selected plugins in each round. The default value is `3`.

## Auto Plugin Selection Example

We show the auto plugin selection mechanism in the following example.

First, we start TaskWeaver with the auto plugin selection mechanism enabled.
```bash
=========================================================
 _____         _     _       __
|_   _|_ _ ___| | _ | |     / /__  ____ __   _____  _____
  | |/ _` / __| |/ /| | /| / / _ \/ __ `/ | / / _ \/ ___/
  | | (_| \__ \   < | |/ |/ /  __/ /_/ /| |/ /  __/ /
  |_|\__,_|___/_|\_\|__/|__/\___/\__,_/ |___/\___/_/
=========================================================
TaskWeaver: I am TaskWeaver, an AI assistant. To get started, could you please enter your request?
Human: 
```

Then we can check the log file `task_weaver.log` in the `logs` folder to see the auto plugin selector is initialized successfully because the `Plugin embeddings generated` message is printed.
```bash
2023-12-18 14:23:44,197 - INFO - Planner initialized successfully
2023-12-18 14:24:10,488 - INFO - Plugin embeddings generated
2023-12-18 14:24:10,490 - INFO - CodeInterpreter initialized successfully.
2023-12-18 14:24:10,490 - INFO - Session 20231218-062343-c18494b1 is initialized
```
We ask TaskWeaver to "search Xbox price for me".
The Planner instructs the Code Interpreter to search Xbox price.

```bash
TaskWeaver: I am TaskWeaver, an AI assistant. To get started, could you please enter your request?
Human: search xbox price for me
>>> [INIT_PLAN]
1. search xbox price
2. report the result to the user <interactively depends on 1>
>>> [PLAN]
1. instruct CodeInterpreter to search xbox price
2. report the result to the user
>>> [CURRENT_PLAN_STEP]
1. instruct CodeInterpreter to search xbox price
>>> [SEND_TO]
CodeInterpreter
>>> [MESSAGE]
Please search xbox price
>>> [PLANNER->CODEINTERPRETER]
Please search xbox price
```

Back to the Code Interpreter, the auto plugin selection mechanism is triggered.
We can check the log file `task_weaver.log` again to see the auto plugin selector selected the top-3 plugins with the highest cosine similarity scores.
```bash
023-12-18 14:24:34,513 - INFO - Planner talk to CodeInterpreter: Please search xbox price using klarna_search plugin
2023-12-18 14:24:34,669 - INFO - Selected plugins: ['klarna_search', 'sql_pull_data', 'paper_summary']
2023-12-18 14:24:34,669 - INFO - Selected plugin pool: ['klarna_search', 'sql_pull_data', 'paper_summary']
```

Then the Code Interpreter will generate the code using the selected plugins.
````bash
>>> [THOUGHT]
ProgramApe will call the klarna_search plugin function to search for Xbox prices.
>>> [PYTHON]
search_results, description = klarna_search(query="xbox")
search_results, description
>>> [VERIFICATION]
NONE
>>> [STATUS]
SUCCESS
>>> [RESULT]
The execution of the generated python code above has succeeded

The result of above Python code after execution is:
(                                                 name    price                                                url                                         attributes
 0             Microsoft Xbox Series X - Black Edition  $399.00  https://www.klarna.com/us/shopping/pl/cl52/495...  [Release Year:2020, Included Accessories:1 gam...
 1                 Microsoft Xbox Series S 1TB - Black  $349.00  https://www.klarna.com/us/shopping/pl/cl52/320...  [Included Accessories:1 gamepad, Media Type:DV...
 ..                                                ...      ...                                                ...                                                ...
 3                      Xbox Series S – Starter Bundle  $239.00  https://www.klarna.com/us/shopping/pl/cl52/320...                                [Platform:Xbox One]
 4   Microsoft Xbox Series X 1TB Console - Diablo I...  $385.58  https://www.klarna.com/us/shopping/pl/cl52/320...  [Release Year:2023, Included Accessories:1 gam...

 [5 rows x 4 columns],
 'The response is a dataframe with the following columns: name, price, url, attributes. The attributes column is a list of tags. The price is in the format of $xx.xx.')
>>> [CODEINTERPRETER->PLANNER]
The following python code has been executed:
```python
search_results, description = klarna_search(query="xbox")
search_results, description
```

The execution of the generated python code above has succeeded

The result of above Python code after execution is:
(                                                 name    price                                                url                                         attributes
 0             Microsoft Xbox Series X - Black Edition  $399.00  https://www.klarna.com/us/shopping/pl/cl52/495...  [Release Year:2020, Included Accessories:1 gam...
 1                 Microsoft Xbox Series S 1TB - Black  $349.00  https://www.klarna.com/us/shopping/pl/cl52/320...  [Included Accessories:1 gamepad, Media Type:DV...
 ..                                                ...      ...                                                ...                                                ...
 3                      Xbox Series S – Starter Bundle  $239.00  https://www.klarna.com/us/shopping/pl/cl52/320...                                [Platform:Xbox One]
 4   Microsoft Xbox Series X 1TB Console - Diablo I...  $385.58  https://www.klarna.com/us/shopping/pl/cl52/320...  [Release Year:2023, Included Accessories:1 gam...

 [5 rows x 4 columns],
 'The response is a dataframe with the following columns: name, price, url, attributes. The attributes column is a list of tags. The price is in the format of $xx.xx.')
```` 

Finally, the Planner will report the result to the user.
```bash
>>> [INIT_PLAN]
1. search xbox price using klarna_search plugin
2. report the result to the user <interactively depends on 1>
>>> [PLAN]
1. instruct CodeInterpreter to search xbox price using klarna_search plugin
2. report the result to the user
>>> [CURRENT_PLAN_STEP]
2. report the result to the user
>>> [SEND_TO]
User
>>> [MESSAGE]
Here are some Xbox prices I found:

1. Microsoft Xbox Series X - Black Edition: $399.00
2. Microsoft Xbox Series S 1TB - Black: $349.00
3. Xbox Series S – Starter Bundle: $239.00
4. Microsoft Xbox Series X 1TB Console - Diablo Immortal Edition: $385.58

Please note that these prices are subject to change and availability.
>>> [PLANNER->USER]
Here are some Xbox prices I found:

1. Microsoft Xbox Series X - Black Edition: $399.00
2. Microsoft Xbox Series S 1TB - Black: $349.00
3. Xbox Series S – Starter Bundle: $239.00
4. Microsoft Xbox Series X 1TB Console - Diablo Immortal Edition: $385.58

Please note that these prices are subject to change and availability.
TaskWeaver: Here are some Xbox prices I found:

1. Microsoft Xbox Series X - Black Edition: $399.00
2. Microsoft Xbox Series S 1TB - Black: $349.00
3. Xbox Series S – Starter Bundle: $239.00
4. Microsoft Xbox Series X 1TB Console - Diablo Immortal Edition: $385.58

Please note that these prices are subject to change and availability.
```
