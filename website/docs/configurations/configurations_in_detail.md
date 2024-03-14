
# More about Configurations

## Planner Configuration

In TaskWeaver, the Planner is responsible for generating a plan to accomplish the user's task. The plan is a sequence of steps, where each step will be executed by the Code Interpreter.
Taken the response from the Code Interpreter or new requests from the user as input, the Planner will update the plan and move on to the next step.


- `planner.example_base_path`:	The folder to store planner examples. The default value is `${AppBaseDir}/planner_examples`. 
If you want to create your own planner examples, you can add them to this folder. More details about `example` can referred to [example](../customization/example/example.md).
- `planner.prompt_compression`: At times, lengthy conversations with the Planner may exceed the input limitations of the LLM model. 
To address this issue, we can compress the chat history and send it to the LLM model. The default value for this setting is `false`.
More details about `prompt_compression` can be referred to [prompt_compression](./compression).
- `planner.skip_planning`: In certain scenarios, there may be no need to use the Planner to generate complex plans for simple tasks. 
For instance, if a user wants to count the rows in a data file, the request can be sent directly to the Code Interpreter. 
When the majority of user requests involve simple tasks, enabling this option will create a dummy plan that is sent alongside the user request to the Code Interpreter directly, without LLM generation process.
The fixed dummy plan is shown in [dummy_plan.json](https://github.com/microsoft/TaskWeaver/blob/main/taskweaver/planner/dummy_plan.json).
Here is an chat example:
`````bash
=========================================================
 _____         _     _       __
|_   _|_ _ ___| | _ | |     / /__  ____ __   _____  _____
  | |/ _` / __| |/ /| | /| / / _ \/ __ `/ | / / _ \/ ___/
  | | (_| \__ \   < | |/ |/ /  __/ /_/ /| |/ /  __/ /
  |_|\__,_|___/_|\_\|__/|__/\___/\__,_/ |___/\___/_/
=========================================================
TaskWeaver: I am TaskWeaver, an AI assistant. To get started, could you please enter your request?
Human: generate 10 random numbers
>>> [MESSAGE]eparing...           <=�=>
Please process this request: generate 10 random numbers
>>> [SEND_TO]
CodeInterpreter
>>> [INIT_PLAN]
1. ask Code Interpreter to handle the request; 2. report the result to user <interactively depends on 1>
>>> [PLAN]
1. ask Code Interpreter to handle user\'s request; 2. report the result to user
>>> [CURRENT_PLAN_STEP]
1. ask Code Interpreter to handle the request
>>> [PLANNER->CODEINTERPRETER]
Please process this request: generate 10 random numbers
>>> [PYTHON]Starting...      
random_numbers = np.random.rand(10)
random_numbers
>>> [VERIFICATION]
NONE
>>> [STATUS]Starting...         
SUCCESS
>>> [RESULT]
The execution of the generated python code above has succeeded

The result of above Python code after execution is:
array([0.65294462, 0.26946084, 0.06244879, 0.78520418, 0.87067657,
       0.24208003, 0.60249788, 0.30921069, 0.83811521, 0.05135891])
>>> [CODEINTERPRETER->PLANNER]
The following python code has been executed:
```python
random_numbers = np.random.rand(10)
random_numbers
```

The execution of the generated python code above has succeeded

The result of above Python code after execution is:
array([0.65294462, 0.26946084, 0.06244879, 0.78520418, 0.87067657,
       0.24208003, 0.60249788, 0.30921069, 0.83811521, 0.05135891])
>>> [INIT_PLAN]ting...      <=�=>     
1. ask Code Interpreter to handle the request; 2. report the result to user <interactively depends on 1>
>>> [PLAN]
1. ask Code Interpreter to handle user's request; 2. report the result to user
>>> [CURRENT_PLAN_STEP]
2. report the result to user
>>> [SEND_TO]
User
>>> [MESSAGE]
The random numbers are as follows: [0.65294462, 0.26946084, 0.06244879, 0.78520418, 0.87067657, 0.24208003, 0.60249788, 0.30921069, 0.83811521, 0.05135891]
>>> [PLANNER->USER]
The random numbers are as follows: [0.65294462, 0.26946084, 0.06244879, 0.78520418, 0.87067657, 0.24208003, 0.60249788, 0.30921069, 0.83811521, 0.05135891]
TaskWeaver: The random numbers are as follows: [0.65294462, 0.26946084, 0.06244879, 0.78520418, 0.87067657, 0.24208003, 0.60249788, 0.30921069, 0.83811521, 0.05135891]
`````


## Session Configration

`session` is the entrance of TaskWeaver. 
It is responsible for the communication between the user and TaskWeaver.
You can refer to [taskweaver_as_a_lib](../usage/library.md) to see how to setup a TaskWeaver session and start chatting with TaskWeaver.


- `max_internal_chat_round_num`: the maximum number of internal chat rounds between Planner and Code Interpreter. 
  If the number of internal chat rounds exceeds this number, the session will be terminated. 
  The default value is `10`.
- `code_interpreter_only`: allow users to directly communicate with the Code Interpreter.
   In this mode, users can only send messages to the Code Interpreter and receive messages from the Code Interpreter.
   Here is an example:

``````bash
 =========================================================
 _____         _     _       __
|_   _|_ _ ___| | _ | |     / /__  ____ __   _____  _____
  | |/ _` / __| |/ /| | /| / / _ \/ __ `/ | / / _ \/ ___/
  | | (_| \__ \   < | |/ |/ /  __/ /_/ /| |/ /  __/ /
  |_|\__,_|___/_|\_\|__/|__/\___/\__,_/ |___/\___/_/
=========================================================
TaskWeaver: I am TaskWeaver, an AI assistant. To get started, could you please enter your request?
Human: generate 10 random numbers
>>> [PYTHON]Starting... 
import numpy as np
random_numbers = np.random.rand(10)
random_numbers
>>> [VERIFICATION]
NONE
>>> [STATUS]Starting...         
SUCCESS
>>> [RESULT]
The execution of the generated python code above has succeeded

The result of above Python code after execution is:
array([0.09918602, 0.68732778, 0.44413814, 0.4756623 , 0.48302334,
       0.8286594 , 0.80994359, 0.35677263, 0.45719317, 0.68240194])
>>> [CODEINTERPRETER->PLANNER]
The following python code has been executed:
```python
import numpy as np
random_numbers = np.random.rand(10)
random_numbers
```

The execution of the generated python code above has succeeded

The result of above Python code after execution is:
array([0.09918602, 0.68732778, 0.44413814, 0.4756623 , 0.48302334,
       0.8286594 , 0.80994359, 0.35677263, 0.45719317, 0.68240194])
TaskWeaver: The following python code has been executed:
```python
import numpy as np
random_numbers = np.random.rand(10)
random_numbers
```

The execution of the generated python code above has succeeded

The result of above Python code after execution is:
array([0.09918602, 0.68732778, 0.44413814, 0.4756623 , 0.48302334,
       0.8286594 , 0.80994359, 0.35677263, 0.45719317, 0.68240194])
``````
- `code_gen_mode`: code generation mode.
  - `plugin_only`: please refer to [plugin_only_mode](../customization/plugin/plugin_only.md) for more details.
  - `cli_only`: allow users to directly communicate with the Command Line Interface (CLI) in natural language.
    CodeInterpreter will generate CLI commands (e.g., bash/powershell), instead of Python code, to fulfill the user's request.
  
    💡It is better to enable `code_interpreter_only` when `cli_only` mode is enabled.
    Here is an example:
``````bash
=========================================================
 _____         _     _       __
|_   _|_ _ ___| | _ | |     / /__  ____ __   _____  _____
  | |/ _` / __| |/ /| | /| / / _ \/ __ `/ | / / _ \/ ___/
  | | (_| \__ \   < | |/ |/ /  __/ /_/ /| |/ /  __/ /
  |_|\__,_|___/_|\_\|__/|__/\___/\__,_/ |___/\___/_/
=========================================================
 TaskWeaver ▶  I am TaskWeaver, an AI assistant. To get started, could you please enter your request?
    Human   ▶  what time is it now
 ╭───< CodeInterpreter] preparing          <=�=>
 ├─► [thought] This command will display the current date and time in the PowerShell command prompt.
 ├─► [python] powershell -Command "Get-Date"
 ╰──● sending message to Planner
 ├──● 
 │   Tuesday, February 27, 2024 11:05:05 AM
 ╰──● sending message to Planner
 TaskWeaver ▶  
Tuesday, February 27, 2024 11:05:05 AM
``````


## Embedding Configration

In TaskWeaver, we support various embedding models to generate embeddings for auto plugin selection.


- `llm.embedding_api_type`: The type of the embedding API. We support the following types:
  - openai
  - qwen
  - ollama
  - sentence_transformers
  - glm

- `llm.embedding_model`: The embedding model name. The model name should be aligned with `llm.embedding_api_type`.
   We only list some embedding models we have tested below:
  - openai
    - text-embedding-ada-002
  - qwen
    - text-embedding-v1
  - ollama
    - llama2
  - sentence_transformers
    - all-mpnet-base-v2
    - multi-qa-mpnet-base-dot-v1
    - all-distilroberta-v1
    - all-MiniLM-L12-v2
    - multi-qa-MiniLM-L6-cos-v1
  - zhipuai
    - embedding-2
You also can use other embedding models supported by the above embedding APIs.