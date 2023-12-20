---
description: Using LLMs from LiteLLM
---


# LiteLLM

:::info
[LiteLLM](https://docs.litellm.ai/) provides a unified interface to call 100+ LLMs using the same Input/Output format, including OpenAI, Huggingface, Anthropic, vLLM, Cohere, and even custom LLM API server. Taking LiteLLM as the bridge, many LLMs can be onboarded to TaskWeaver. Here we use the OpenAI Proxy Server provided by LiteLLM to make configuration.
:::

1. Install LiteLLM Proxy and configure the LLM server by following the instruction [here](https://docs.litellm.ai/docs/proxy/quick_start). In general, there are a few steps:
    1. Install the package `pip install litellm[proxy]`
    2. Setup the API key and other necessary environment variables which vary by LLM. Taking [Cohere](https://cohere.com/) as an example, it is required to setup `export COHERE_API_KEY=my-api-key`.
    3. Run LiteLLM proxy server by `litellm --model MODEL_NAME --drop_params`, for example, in Cohere, the model name can be `command-nightly`. The `drop-params` argument is used to ensure the API compatibility. Then, a server will be automatically started on `http://0.0.0.0:8000`.

:::tip
The full list of supported models by LiteLLM can be found in the [page](https://docs.litellm.ai/docs/providers).
:::


2. Add the following content to your `taskweaver_config.json` file:

```json showLineNumbers
{
  "llm.api_base": "http://0.0.0.0:8000",
  "llm.api_key": "anything",
  "llm.model": "gpt-3.5-turbo"
}
```

:::info
`llm.api_key` and `llm.model` are mainly used as placeholder for API call, whose actual values are not used. If the configuration does not work, please refer to LiteLLM [documents](https://docs.litellm.ai/docs/proxy/quick_start) to locally test whether you can send requests to the LLM. 
:::


3. Open a new terminal, start TaskWeaver and chat.
You can refer to the [Quick Start](../quickstart.md) for more details.