---
description: Using LLMs from Anthropic (Claude)
---

# Anthropic (Claude)

1. Create an account on [Anthropic](https://www.anthropic.com/) and get your API key from the [Anthropic Console](https://console.anthropic.com/settings/keys).

2. Add the following to your `taskweaver_config.json` file:

```json showLineNumbers
{
  "llm.api_type": "anthropic",
  "llm.api_base": "https://api.anthropic.com/v1/messages",
  "llm.api_key": "YOUR_API_KEY",
  "llm.model": "claude-3-opus"
}
```

:::tip
`llm.model` is the model name you want to use. You can find the list of available Claude models in the [Anthropic API documentation](https://docs.anthropic.com/claude/reference/selecting-a-model).
:::

:::info
Anthropic's Claude API doesn't have a specific `response_format` parameter like OpenAI. If you need structured output, you should instruct Claude to respond in a specific format (e.g., JSON) within your prompts.
:::

:::caution
Anthropic doesn't provide a native embedding service. If you need embeddings, you'll need to configure a different service for that functionality.
:::

3. Start TaskWeaver and chat with TaskWeaver using Claude.
   You can refer to the [Quick Start](../quickstart.md) for more details.

Remember to replace `YOUR_API_KEY` with your actual Anthropic API key.
