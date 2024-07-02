
# More about Configurations
More details about important configurations.

## Planner Configuration

- `planner.example_base_path`:	The folder to store planner examples. The default value is `${AppBaseDir}/planner_examples`. 
If you want to create your own planner examples, you can add them to this folder. More details about `example` can referred to [example](../customization/example/example.md).
- `planner.prompt_compression`: At times, lengthy conversations with the Planner may exceed the input limitations of the LLM model. 
To address this issue, we can compress the chat history and send it to the LLM model. The default value for this setting is `false`.
More details about `prompt_compression` can be referred to [prompt_compression](../advanced/compression).
- `planner.use_experience`: Whether to use experience summarized from the previous chat history in planner. The default value is `false`.
- `planner.llm_alias`: The alias of the LLM used by the Planner. If you do not specify the LLM for the Planner, the primary LLM will be used by default.


## Session Configuration

- `session.max_internal_chat_round_num`: the maximum number of internal chat rounds between Planner and Code Interpreter. 
  If the number of internal chat rounds exceeds this number, the session will be terminated. 
  The default value is `10`.
- `session.roles`: the roles included for the conversation. The default value is `["planner", "code_interpreter"]`.
  - TaskWeaver has 3 code interpreters: 
    - `code_interpreter`: it will generate Python code to fulfill the user's request. This is the default code interpreter.
    - `code_interpreter_plugin_only`: please refer to [plugin_only_mode](../advanced/plugin_only.md) for more details.
    - `code_interpreter_cli_only`: allow users to directly communicate with the Command Line Interface (CLI) in natural language. 
      Please refer to [cli_only_mode](../advanced/cli_only.md) for more details.
  - If you do not specify `planner` in the roles, you will enter the "no-planner" mode. 
    It allows users to directly communicate with the worker role, such as `code_interpreter`.
    In this mode, users can only send messages to the `CodeInterpreter` and receive messages from the `CodeInterpreter`.
    Note that only single worker role is allowed in the "no-planner" mode because all user requests will be sent to the worker role directly.
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


## Embedding Configuration

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


## OpenAI Configuration

Today, more and more inference frameworks support OpenAI compatible APIs. However, different models
may have different configurations. Here are some supported configurations for other models adapted 
for OpenAI API.

- `llm.openai.support_system_role`: Whether to support system role in the conversation. The default value is `True`. For
the models that do not support system role, you can set this value to `False`, and the system role will be replaced by the user role. 
- `llm.openai.require_alternative_roles`: Whether to require alternative roles in the conversation. The default value is `False`.
We notice that some models may require exactly alternative roles in the conversation. If you set this value to `True`, the system will
check consecutive `user` messages in the conversation history. If there is, the system will add a dummy `assistant` message in between.
- `llm.openai.support_constrained_generation`: Whether to support constrained generation in the conversation. The default value is `False`.
Some inferencing frameworks like [vllm](https://docs.vllm.ai/en/stable/serving/openai_compatible_server.html) and [llama.cpp](https://github.com/ggerganov/llama.cpp?tab=readme-ov-file#constrained-output-with-grammars)
support constrained generation. Currently, we only support vllm. If you want to use this feature, you can set this value to `True`.
- `llm.openai.json_schema_enforcer`: This is configured together with `llm.openai.support_constrained_generation`. If you want to use
constrained generation. There are two valid options: `lm-format-enforcer` and `outlines`.