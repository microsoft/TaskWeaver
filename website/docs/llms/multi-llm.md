# Multi LLM APIs

In some cases, you may want to use different LLMs for different components. 
For example, you may want to use OpenAI GPT-4 for the Planner but use Google gemini-pro for the CodeInterpreter.
In this part, we show you how to use different LLMs for different components.

If you need only one LLM, you can have only the primary LLM settings in the `taskweaver_config.json` file.
If you need multiple LLMs, you need to have `ext_llms.llm_configs` in the `taskweaver_config.json` file to specify the extra LLMs for different components.
In the following, we show you how to configure the `taskweaver_config.json` file to use multiple LLMs.
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

- The primary LLM settings are specified in the `llm.` fields and it is mandatory.
- `ext_llms.llm_configs` is optional and is a dict of extra LLMs for different components. If you do not specify it, only the primary LLM will be used.
 

Specify the LLMs for different components in the `taskweaver_config.json`.
For example, we want to use OpenAI GPT-4 for the Planner and use Google gemini-pro for the CodeInterpreter.
```json
"planner.llm_alias": "llm_A",
"code_generator.llm_alias": "llm_B"
```
:::tip
If you do not specify the LLM for a component, the primary LLM will be used by default.
In the above example, `GPT-3.5-turbo-1106` will be used for both the Planner and the CodeInterpreter.
:::


