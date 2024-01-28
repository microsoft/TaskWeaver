# GLM

1. GLM (ChatGLM) is a LLM developed by Zhipu AI and Tsinghua KEG. Go to [ZhipuAI](https://open.bigmodel.cn/) and register an account and get the API key. More details can be found [here](https://open.bigmodel.cn/overview).
2. Install the required packages dashscope.
```bash
pip install zhipuai
```
3. Add the following configuration to `taskweaver_config.json`:
```json showLineNumbers
{
  "llm.api_type": "zhipuai",
  "llm.model": "glm-4",
  "llm.embedding_model": "embedding-2",
  "llm.embedding_api_type": "zhipuai",
  "llm.api_key": "YOUR_API_KEY"
}
```
NOTE: `llm.model` is the model name of zhipuai  API. 
You can find the model name in the [GLM model list](https://open.bigmodel.cn/dev/api#language).

4. Start TaskWeaver and chat with TaskWeaver. 
You can refer to the [Quick Start](../quickstart.md) for more details.
