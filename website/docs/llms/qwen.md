# QWen

TaskWeaver supports QWen LLM and embedding API.

## How to use QWen LLM and embedding API

1. Go to [QWen](https://help.aliyun.com/zh/dashscope/developer-reference/activate-dashscope-and-create-an-api-key?spm=a2c4g.11186623.0.0.7b5749d72j3SYU) and register an account and get the API key.
2. Run `pip install dashscope` to install the required packages.
3. Add the following configuration to `taskweaver_config.json`:
```json
{
    "llm.api_type": "qwen",
    "llm.model": "qwen-max", 
    "llm.api_key": "YOUR_API_KEY",
    "llm.embedding_api_type": "qwen",
    "llm.embedding_model": "text-embedding-v1"
}
```
NOTE: `llm.model` is the model name of QWen LLM and `llm.embedding_model` is the model name of QWen embedding API. 
You can find the model name in the [QWen LLM model list](https://help.aliyun.com/zh/dashscope/developer-reference/model-square/?spm=a2c4g.11186623.0.0.35a36ffdt97ljI).

4. Start TaskWeaver and chat with TaskWeaver.