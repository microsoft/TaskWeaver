from injector import Injector

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.llm import LLMModuleConfig
from taskweaver.logging import LoggingModule
from taskweaver.utils.embedding import EmbeddingGenerator, EmbeddingModelConfig


def test_sentence_transformer_embedding():
    app_injector = Injector()
    app_config = AppConfigSource(
        config={
            "embedding_model.embedding_model_type": "sentence_transformer",
            "embedding_model.embedding_model": "all-mpnet-base-v2",
            "llm.api_key": "test_key",
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    embedding_generator = app_injector.create_object(EmbeddingGenerator)

    text = "This is a test sentence."
    embedding = embedding_generator.get_embedding(text)

    assert len(embedding) == 768


def test_openai_embedding():
    app_injector = Injector()
    app_config = AppConfigSource(
        config={
            "embedding_model.embedding_model_type": "openai",
            "embedding_model.embedding_model": "text-embedding-ada-002",
            # need to configure llm.api_key in the env or config file to run this test
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    embedding_generator = app_injector.create_object(EmbeddingGenerator)

    text = "This is a test sentence."
    embedding = embedding_generator.get_embedding(text)

    assert len(embedding) == 1536
