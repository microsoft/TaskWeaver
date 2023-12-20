# Gemini

1. Create an account on [Google AI](https://ai.google.dev/) and get your API key.
2. Add the following content to your `taskweaver_config.json` file:
```json showLineNumbers
{
"llm.api_type": "google_genai",
"llm.google_genai.api_key": "YOUR_API_KEY",
"llm.google_genai.model": "gemini-pro"
}
```


3. Start TaskWeaver and chat with TaskWeaver.
You can refer to the [Quick Start](../quickstart.md) for more details.



