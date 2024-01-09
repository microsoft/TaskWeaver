from typing import Any, List

from injector import inject

from taskweaver.llm.base import EmbeddingService, LLMServiceConfig


class SentenceTransformerServiceConfig(LLMServiceConfig):
    def _configure(self) -> None:
        self._set_name("sentence_transformers")

        self.embedding_model_candidates = [
            "all-mpnet-base-v2",
            "multi-qa-mpnet-base-dot-v1",
            "all-distilroberta-v1",
            "all-MiniLM-L12-v2",
            "multi-qa-MiniLM-L6-cos-v1",
        ]

        shared_embedding_model = self.llm_module_config.embedding_model
        self.embedding_model = self._get_enum(
            "embedding_model",
            self.embedding_model_candidates,
            shared_embedding_model if shared_embedding_model is not None else self.embedding_model_candidates[0],
            required=False,
        )
        assert (
            self.embedding_model in self.embedding_model_candidates
        ), f"embedding model {self.embedding_model} is not supported"


class SentenceTransformerService(EmbeddingService):
    @inject
    def __init__(self, config: SentenceTransformerServiceConfig):
        self.config = config
        self._initialized: bool = False

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self.embedding_model: Any = SentenceTransformer(self.config.embedding_model)
        except Exception:
            raise Exception(
                "Package sentence_transformers is required for using embedding. "
                "Please install it using pip install sentence_transformers",
            )
        self._initialized = True

    def get_embeddings(self, strings: List[str]) -> List[List[float]]:
        if not self._initialized:
            self._load_model()

        embeddings = self.embedding_model.encode(strings)
        embeddings = embeddings.tolist()
        return embeddings
