# Multi LLM APIs for Different Components

In some cases, you may want to use different LLMs for different components. 
For example, you may want to use OpenAI GPT-4 for the Planner but use Google gemini-pro for the CodeInterpreter.
In this section, we will show you how to use different LLMs for different components.

## Usage

1. Configure the primary LLM and extra LLMs settings in the `taskweaver_config.json` file under `project` directory, just as follows:
```json
"llm.api_type":"openai",
"llm.api_base": "https://api.openai.com/v1",
"llm.api_key": "YOUR_API_KEY",
"llm.model": "gpt-3.5-turbo-1106",
"llm.response_format": "json_object"
"ext_llms.llm_configs": {
    "llm_A":
        {
            "llm.api_type": "openai",
            "llm.api_base": "https://api.openai.com/v1",
            "llm.api_key": "YOUR_API_KEY",
            "llm.model": "gpt-4-1106-preview",
            "llm.response_format": "json_object",
        },
    "llm_B":
        {
            "llm.api_type": "google_genai",
            "llm.api_key": "YOUR_API_KEY",
            "llm.model": "gemini-pro",
        },
},
```
Notes:
- `ext_llms.llm_configs` is a dict of extra LLMs for different components. It is an optional field. If you do not specify it, only the primary LLM will be used.
- For each LLM setting, please should follow the configuration method described in each LLM configuration page.
- Besides the extra LLMs, you should also configure the primary LLM settings in the `taskweaver_config.json`, just as shown in the top 5 lines in the above code snippet.

2. Specify the LLMs for different components in the `taskweaver_config.json`.
For example, we want to use OpenAI GPT-4 for the Planner and use Google gemini-pro for the CodeInterpreter.
```json
"planner.llm_alias": "llm_A",
"code_generator.llm_alias": "llm_B"
```
Notes:
- If you do not specify the LLM for a component, the primary LLM will be used by default.
In this case, `GPT-3.5-turbo-1106` will be used for both the Planner and the CodeInterpreter, if you do not specify the LLM for them.


