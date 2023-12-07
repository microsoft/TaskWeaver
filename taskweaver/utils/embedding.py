from injector import inject

from taskweaver.config.module_config import ModuleConfig
from taskweaver.llm import LLMApi


class EmbeddingModuleConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("embedding_model")
        self.embedding_model_type = self._get_enum(
            "embedding_model_type",
            ["sentence_transformer", "openai"],
            "sentence_transformer",
        )
        self.embedding_model_candidates = {
            "sentence_transformer": [
                "all-mpnet-base-v2",
                "multi-qa-mpnet-base-dot-v1",
                "all-distilroberta-v1",
                "all-MiniLM-L12-v2",
                "multi-qa-MiniLM-L6-cos-v1",
            ],
            "openai": [
                "text-embedding-ada-002",
            ],
        }
        self.embedding_model = self._get_enum(
            "embedding_model",
            self.embedding_model_candidates[self.embedding_model_type],
            self.embedding_model_candidates[self.embedding_model_type][0],
        )


class EmbeddingGenerator:
    @inject
    def __init__(self, config: EmbeddingModuleConfig, llm_api: LLMApi):
        self.config = config
        self.llm_api = llm_api

        if self.config.embedding_model_type == "sentence_transformer":
            try:
                from sentence_transformers import SentenceTransformer

                self.embedding_model = SentenceTransformer(self.config.embedding_model)
            except Exception:
                raise Exception(
                    "Package sentence_transformers is required for using embedding. "
                    "Please install it using pip install sentence_transformers",
                )
        elif self.config.embedding_model_type == "openai":
            self.client = self.llm_api.get_client()

    def get_embedding(self, string: str) -> list:
        def get_openai_embedding(string: str):
            return self.client.embeddings.create(input=[string], model=self.config.embedding_model).data[0].embedding

        def get_ST_embedding(string: str):
            embedding = self.embedding_model.encode(string)
            embedding = embedding.tolist()

            return embedding

        embedding_model_type = self.config.embedding_model_type
        if embedding_model_type == "sentence_transformer":
            embedding_vec = get_ST_embedding(string)
            return embedding_vec
        elif embedding_model_type == "openai":
            embedding_vec = get_openai_embedding(string)
            return embedding_vec
        else:
            raise ValueError(
                "No valid embedding model type provided.",
            )
