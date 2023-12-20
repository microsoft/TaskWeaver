# Ollama

## How to use Ollama LLM API

1. Go to [Ollama](https://github.com/jmorganca/ollama) and follow the instructions to set up a LLM model on your local environment.
We recommend deploying the LLM with a parameter scale exceeding 13 billion for enhanced performance.
2. Add following configuration to `taskweaver_config.json`:
```json
{
    "llm.api_base": "http://localhost:11434",
    "llm.api_key": "ARBITRARY_STRING",
    "llm.api_type": "ollama",
    "llm.model": "llama2:13b"
}
```
NOTE: `llm.api_base` is the URL started in the Ollama LLM server and `llm.model` is the model name of Ollama LLM. 
3. Start TaskWeaver and chat with TaskWeaver. 
You can refer to the [Quick Start](../quickstart.md) for more details.
