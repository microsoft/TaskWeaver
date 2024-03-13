# Embedding

In TaskWeaver, we support various embedding models to generate embeddings for auto plugin selection.


## Embedding Configration

- `llm.embedding_api_type`: The type of the embedding API. We support the following types:
  - openai
  - qwen
  - ollama
  - sentence_transformers
  - glm

- `llm.embedding_model`: The embedding model name. The model name should be aligned with `llm.embedding_api_type`.
   We only list some embedding models we have tested below:
  - openai
    - text-embedding-ada-002
  - qwen
    - text-embedding-v1
  - ollama
    - llama2
  - sentence_transformers
    - all-mpnet-base-v2
    - multi-qa-mpnet-base-dot-v1
    - all-distilroberta-v1
    - all-MiniLM-L12-v2
    - multi-qa-MiniLM-L6-cos-v1
  - zhipuai
    - embedding-2
You also can use other embedding models supported by the above embedding APIs.