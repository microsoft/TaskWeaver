from injector import Injector

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.llm.openai import OpenAIService
from taskweaver.llm.sentence_transformer import SentenceTransformerService


def test_sentence_transformer_embedding():
    app_injector = Injector([])
    app_config = AppConfigSource(
        config={
            "llm.embedding_api_type": "sentence_transformer",
            "llm.embedding_model": "all-mpnet-base-v2",
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    sentence_transformer_service = app_injector.create_object(SentenceTransformerService)

    text_list = ["This is a test sentence.", "This is another test sentence."]
    embedding1 = sentence_transformer_service.get_embeddings(text_list)

    assert len(embedding1) == 2
    assert len(embedding1[0]) == 768
    assert len(embedding1[1]) == 768


def test_openai_embedding():
    app_injector = Injector()
    app_config = AppConfigSource(
        config={
            "llm.embedding_api_type": "openai",
            "llm.embedding_model": "text-embedding-ada-002",
            # need to configure llm.api_key in the env or config file to run this test
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    openai_service = app_injector.create_object(OpenAIService)

    text_list = ["This is a test sentence.", "This is another test sentence."]
    embedding1 = openai_service.get_embeddings(text_list)

    assert len(embedding1) == 2
    assert len(embedding1[0]) == 1536
    assert len(embedding1[1]) == 1536
