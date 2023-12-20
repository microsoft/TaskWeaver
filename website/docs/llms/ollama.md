# Ollama

## How to use Ollama LLM and embedding API

1. Go to [Ollama](https://github.com/jmorganca/ollama) and follow the instructions to set up a LLM model on your local environment.
We recommend deploying the LLM with a parameter scale exceeding 13 billion for enhanced performance.
2. Add following configuration to `taskweaver_config.json`:
```json
{
    "llm.api_base": "http://localhost:11434",
    "llm.api_key": "ARBITRARY_STRING",
    "llm.api_type": "ollama",
    "llm.model": "llama2:13b",
    "llm.embedding_api_type": "ollama",
    "llm.embedding_model": "llama2"
}
```
NOTE: `llm.api_base` is the base URL set in the Ollama LLM API. 
3. Start TaskWeaver and chat with TaskWeaver.