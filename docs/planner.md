# Planner

In TaskWeaver, the Planner is responsible for generating a plan to accomplish the user's task.
The plan is a sequence of steps, where each step will be executed by the Code Interpreter.
Taken the response from the Code Interpreter or new requests from the user as input, the Planner will update the plan and move on to the next step.

## Planner Configuration

- `planner.example_base_path`:	The folder to store planner examples. The default value is `${AppBaseDir}/planner_examples`. 
If you want to create your own planner examples, you can add them to this folder. More details about `example` can referred to [example](./example.md).
- `planner.prompt_compression`: At times, lengthy conversations with the Planner may exceed the input limitations of the LLM model. 
To address this issue, we can compress the chat history and send it to the LLM model. The default value for this setting is `false`.
More details about `prompt_compression` can be referred to [prompt_compression](./compression.md).
- `planner.skip_planning`: In certain scenarios, there may be no need to use the Planner to generate complex plans for simple tasks. 
For instance, if a user wants to count the rows in a data file, the request can be sent directly to the Code Interpreter. 
When the majority of user requests involve simple tasks, enabling this option will create a dummy plan that is sent alongside the user request to the Code Interpreter directly, without LLM generation process.
The fixed dummy plan is shown in [dummy_plan.json](../taskweaver/planner/dummy_plan.json).
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
1. ask Code Interpreter to handle user's request; 2. report the result to user
>>> [CURRENT_PLAN_STEP]
1. ask Code Interpreter to handle the request
>>> [PLANNER->CODEINTERPRETER]
Please process this request: generate 10 random numbers
>>> [PYTHON]tarting...        <=�=>   
random_numbers = np.random.rand(10)
random_numbers
>>> [VERIFICATION]
NONE
>>> [STATUS]tarting... <=�=>          
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