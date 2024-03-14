# Planner

In TaskWeaver, the Planner is responsible for generating a plan to accomplish the user's task.
The plan is a sequence of steps, where each step will be executed by the Code Interpreter.
Taken the response from the Code Interpreter or new requests from the user as input, the Planner will update the plan and move on to the next step.

## Planner Configuration

- `planner.example_base_path`:	The folder to store planner examples. The default value is `${AppBaseDir}/planner_examples`. 
If you want to create your own planner examples, you can add them to this folder. More details about `example` can referred to [example](./customization/example/example.md).
- `planner.prompt_compression`: At times, lengthy conversations with the Planner may exceed the input limitations of the LLM model. 
To address this issue, we can compress the chat history and send it to the LLM model. The default value for this setting is `false`.
More details about `prompt_compression` can be referred to [prompt_compression](./compression).