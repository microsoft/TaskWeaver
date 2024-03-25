# GroqChat

1. Groq was founded in 2016 by Chief Executive Officer `Jonathan Ross`, a former Google LLC engineer who invented the search giant's TPU machine learning processors. Go to [Groq](https://groq.com/) and register an account and get the API key from [here](https://console.groq.com/keys). More details can be found [here](https://console.groq.com/docs/quickstart).
2. Install the required packages `groq`.
```bash
pip install groq
```
3. Add the following configuration to `taskweaver_config.json`:
```json showLineNumbers
{
    "llm.api_base": "https://console.groq.com/",
    "llm.api_key": "YOUR_API_KEY",
    "llm.api_type": "groq",
    "llm.model": "mixtral-8x7b-32768"
}
```

:::tip
NOTE: `llm.model` is the model name of Groq LLM API. 
You can find the model name in the [Groq LLM model list](https://console.groq.com/docs/models).
:::

4. Start TaskWeaver and chat with TaskWeaver. 
You can refer to the [Quick Start](../quickstart.md) for more details.
