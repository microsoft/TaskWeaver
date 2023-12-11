from injector import Injector

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.utils.embedding import EmbeddingGenerator


def test_sentence_transformer_embedding():
    app_injector = Injector([])
    app_config = AppConfigSource(
        config={
            "embedding_model.embedding_model_type": "sentence_transformer",
            "embedding_model.embedding_model": "all-mpnet-base-v2",
            "llm.api_key": "test_key",
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    embedding_generator = app_injector.create_object(EmbeddingGenerator)

    text_list = ["This is a test sentence.", "This is another test sentence."]
    embedding1 = embedding_generator.get_embedding(text_list)

    assert len(embedding1) == 2
    assert len(embedding1[0]) == 768
    assert len(embedding1[1]) == 768

    text = "This is a test sentence."
    embedding2 = embedding_generator.get_embedding(text)
    assert len(embedding2) == 768


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

    text_list = ["This is a test sentence.", "This is another test sentence."]
    embedding1 = embedding_generator.get_embedding(text_list)

    assert len(embedding1) == 2
    assert len(embedding1[0]) == 1536
    assert len(embedding1[1]) == 1536

    text = "This is a test sentence."
    embedding2 = embedding_generator.get_embedding(text)
    assert len(embedding2) == 1536
