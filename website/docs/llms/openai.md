---
description: Using LLMs from OpenAI
---
# OpenAI

1. Create an account on [OpenAI](https://beta.openai.com/) and get your [API key](https://platform.openai.com/api-keys).
2. Add the following to your `taskweaver_config.json` file:
```json showLineNumbers
{
  "llm.api_type":"openai",
  "llm.api_base": "https://api.openai.com/v1",
  "llm.api_key": "YOUR_API_KEY",
  "llm.model": "gpt-4-1106-preview",
  "llm.response_format": "json_object"
}
```
:::tip
`llm.model` is the model name you want to use.
You can find the list of models [here](https://platform.openai.com/docs/models).
:::

:::info
For `gpt-4-1106-preview` and `gpt-3.5-turbo-1106`, `llm.response_format` can be set to `json_object`.
However, for the earlier models which do not support JSON response explicitly, `llm.response_format` should be set to `null`.
:::
3. Start TaskWeaver and chat with TaskWeaver.
You can refer to the [Quick Start](../quickstart.md) for more details.