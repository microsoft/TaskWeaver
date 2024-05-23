---
description: Using LLMs from Keywords AI and have better observability.
---


# Keywords AI

:::info
[Keywords AI](https://keywordsai.co/) is a unified developer platform where you can call 150+ LLM using the OpenAI format with one API key and get insights into your AI products. With 2 lines of code, you can build better AI products with complete observability.
:::


1. Sign in [Keywords AI](https://keywordsai.co/) and generate an API key to call 150+ LLMs. 

:::tip
The full list of supported models by Keywords AI can be found in the [page](https://platform.keywordsai.co/platform/models).
:::


2. Add the following content to your `taskweaver_config.json` file:

```json showLineNumbers
{
  "llm.api_type":"openai",
  "llm.api_base": "https://api.keywordsai.co/api/",
  "llm.api_key": "Your_Keywords_AI_API_Key",
  "llm.model": "gpt-4o", 
}
```

:::info
If the configuration does not work, please refer to Keywords AI [documents](https://docs.keywordsai.co/get-started/quick-start) to locally test whether you can send requests to the LLM. 
:::


3. Open a new terminal, start TaskWeaver and chat.
You can refer to the [Quick Start](../quickstart.md) for more details.

4. Suppose you want your AI products to be more robust and have better observability, such as having fallback models when primary models fail or knowing more about user activities. In that case, you can add parameters like fallback_models and customer_identifier in the extra_body param from OpenAI.