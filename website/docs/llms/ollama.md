# Ollama

1. Go to [Ollama](https://github.com/jmorganca/ollama) and follow the instructions to serve a LLM model on your local environment.
We provide a short example to show how to configure the ollama in the following, which might change if ollama makes updates.

```bash title="install ollama and serve LLMs in local" showLineNumbers
## Install ollama on Linux & WSL2
curl https://ollama.ai/install.sh | sh
## Run the serving
ollama serve
```
Open another terminal and run:
```bash
ollama run llama2:13b
```
:::tip
We recommend deploying the LLM with a parameter scale exceeding 13B for enhanced performance (such as Llama 2 13B).
:::

:::info
When serving LLMs via Ollama, it will by default start a server at `http://localhost:11434`, which will later be used as the API base in `taskweaver_config.json`.
:::

2. Add following configuration to `taskweaver_config.json`:
```json showLineNumbers
{
    "llm.api_base": "http://localhost:11434",
    "llm.api_key": "ARBITRARY_STRING",
    "llm.api_type": "ollama",
    "llm.model": "llama2:13b"
}
```
NOTE: `llm.api_base` is the URL started in the Ollama LLM server and `llm.model` is the model name of Ollama LLM, it should be same as the one you served before. 

3. Start TaskWeaver and chat with TaskWeaver. 
You can refer to the [Quick Start](../quickstart.md) for more details.
